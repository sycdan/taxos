import hashlib
import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from functools import wraps
from uuid import uuid4

from flask import Flask, Response, request
from flask_cors import CORS
from google.protobuf.json_format import MessageToDict, Parse
from google.protobuf.timestamp_pb2 import Timestamp
from taxos.access.authenticate_tenant.command import AuthenticateTenant
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.repo.load.query import LoadBucketRepo
from taxos.bucket.update.command import UpdateBucket
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.entity import ReceiptRef
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.query import LoadReceiptRepo
from taxos.receipt.update.command import UpdateReceipt
from taxos.tools import json as domain_json

from api.v1 import taxos_service_pb2 as messages

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


def message_to_json(message) -> str:
  message_dict = MessageToDict(
    message,
    preserving_proto_field_name=False,
    always_print_fields_with_no_presence=True,
  )
  return json.dumps(message_dict)


def make_timestamp(value: datetime) -> Timestamp:
  ts = Timestamp()
  ts.FromDatetime(value)
  return ts


def get_text(data, *keys, default: str = ""):
  for key in keys:
    if key in data:
      return str(data[key])
  return default


def get_start_date(data):
  return get_text(data, "start_date", "startDate") or None


def get_end_date(data):
  return get_text(data, "end_date", "endDate") or None


def get_timezone(data):
  return str(get_text(data, "timezone", "tz", "time zone", "timeZone", "timezone", default="UTC"))


def require_auth(f):
  """Decorator to require authentication via access token in headers."""

  @wraps(f)
  def decorated_function(*args, **kwargs):
    # Get token from Authorization header (format: "Bearer <token_hash>")
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
      logger.warning("Missing or invalid Authorization header")
      return Response(
        json.dumps({"error": "Missing or invalid Authorization header"}),
        status=401,
        content_type="application/json",
      )

    token_hash = auth_header[7:]  # Remove "Bearer " prefix

    try:
      tenant = AuthenticateTenant(token_hash).execute()
      context = Context(tenant=tenant)
      set_context(context)
      return f(*args, **kwargs)
    except Exception as e:
      logger.warning(f"Authentication failed: {e}")
      return Response(
        json.dumps({"error": "Invalid or expired access token"}),
        status=401,
        content_type="application/json",
      )

  return decorated_function


def _parse_timestamp(value) -> datetime:
  if isinstance(value, str) and value:
    try:
      return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
      pass

  if isinstance(value, dict):
    seconds = value.get("seconds")
    nanos = value.get("nanos", 0)
    if seconds is not None:
      return datetime.fromtimestamp(float(seconds) + (float(nanos) / 1_000_000_000), tz=timezone.utc)

  return datetime.now(timezone.utc)


def _parse_allocations(values: list[dict]) -> set:
  """Convert API allocation dicts to domain Allocation objects."""
  from taxos.allocation.entity import Allocation
  from taxos.bucket.entity import BucketRef

  allocations = set()
  for item in values or []:
    if not isinstance(item, dict):
      continue
    bucket_guid = item.get("bucket") or item.get("bucket_guid") or item.get("bucketGuid") or ""
    if not bucket_guid:
      continue
    amount = float(item.get("amount", 0))
    allocations.add(Allocation(bucket=BucketRef(bucket_guid), amount=amount))
  return allocations


@app.route("/taxos.v1.TaxosApi/ListBuckets", methods=["POST"])
@require_auth
def list_buckets():
  logger.info("ListBuckets called via ConnectRPC")
  try:
    request_data = request.get_json() or {}
    bucket_summaries: list[messages.BucketSummary] = []

    # Always return all buckets
    repo = LoadBucketRepo().execute()

    # Calculate total amount and receipt count for each bucket
    for bucket in repo.index.values():
      receipt_repo = LoadReceiptRepo(
        start_date=get_start_date(request_data),
        end_date=get_end_date(request_data),
        timezone=get_timezone(request_data),
        bucket=bucket,
      ).execute()

      total_amount = sum(
        sum(a.amount for a in r.allocations if a.bucket.guid == bucket.guid) for r in receipt_repo.receipts
      )
      receipt_count = len(receipt_repo.receipts)
      bucket_summaries.append(
        messages.BucketSummary(
          bucket=messages.Bucket(
            guid=bucket.guid.hex,
            name=bucket.name,
          ),
          total_amount=total_amount,
          receipt_count=receipt_count,
        )
      )

    logger.info(f"Returning {len(bucket_summaries)} buckets")
    response_message = messages.ListBucketsResponse(buckets=bucket_summaries)
    return Response(message_to_json(response_message), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to list buckets: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/CreateBucket", methods=["POST"])
@require_auth
def create_bucket():
  logger.info("CreateBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket = CreateBucket(
      get_text(request_data, "name", default=uuid4().hex[:8]),
    ).execute()
    bucket_message = messages.Bucket(
      guid=bucket.guid.hex,
      name=bucket.name,
    )
    return Response(message_to_json(bucket_message), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to create bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/CreateReceipt", methods=["POST"])
@require_auth
def create_receipt():
  logger.info("CreateReceipt called via ConnectRPC")
  try:
    request_data = request.get_json() or {}
    allocations = _parse_allocations(request_data.get("allocations", []))

    receipt = CreateReceipt(
      vendor=get_text(request_data, "vendor", default=""),
      total=float(request_data.get("total", 0)),
      date=get_text(request_data, "date"),
      timezone=get_timezone(request_data),
      allocations=allocations,
      vendor_ref=get_text(request_data, "ref", default=""),
      notes=get_text(request_data, "notes", default=""),
      hash=get_text(request_data, "hash", default=""),
    ).execute()

    receipt_message = messages.Receipt(
      guid=receipt.guid.hex,
      vendor=receipt.vendor,
      total=receipt.total,
      date=make_timestamp(receipt.date),
      timezone=receipt.timezone,
      allocations=[
        messages.ReceiptAllocation(
          bucket=allocation.bucket.guid.hex,
          amount=allocation.amount,
        )
        for allocation in receipt.allocations
      ],
      vendor_ref=receipt.vendor_ref,
      notes=receipt.notes,
      hash=receipt.hash,
    )
    return Response(message_to_json(receipt_message), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to create receipt: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/GetBucket", methods=["POST"])
@require_auth
def get_bucket():
  logger.info("GetBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket_ref = BucketRef(request_data.get("guid", ""))
    bucket = LoadBucket(ref=bucket_ref).execute()

    response = messages.Bucket(
      guid=bucket.guid.hex,
      name=bucket.name,
    )
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to get bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=404, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/UpdateBucket", methods=["POST"])
@require_auth
def update_bucket():
  logger.info("UpdateBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket_ref = BucketRef(request_data.get("guid", ""))

    try:
      bucket = UpdateBucket(ref=bucket_ref, name=request_data.get("name", "")).execute()
    except Bucket.DoesNotExist:
      return Response(json.dumps({"error": "Bucket not found"}), status=404, content_type="application/json")

    bucket_message = Parse(domain_json.dumps(bucket), messages.Bucket())
    return Response(message_to_json(bucket_message), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to update bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/ListReceipts", methods=["POST"])
@require_auth
def list_receipts():
  logger.info("ListReceipts called via ConnectRPC")
  try:
    request_data = request.get_json() or {}
    bucket_guid = get_text(request_data, "bucket", "bucket_guid", "bucketGuid", "bucket_ref", "bucketRef")

    start_date = None
    end_date = None
    if start_date_value := get_start_date(request_data):
      start_date = _parse_timestamp(start_date_value)
    if end_date_value := get_end_date(request_data):
      end_date = _parse_timestamp(end_date_value)
    timezone = get_timezone(request_data)

    repo: ReceiptRepo = LoadReceiptRepo(
      start_date=start_date,
      end_date=end_date,
      timezone=timezone,
      bucket=bucket_guid or None,
      unallocated_only=not bucket_guid,
    ).execute()

    receipt_messages = []
    for receipt in repo.receipts:
      receipt_message = messages.Receipt(
        guid=receipt.guid.hex,
        vendor=receipt.vendor,
        total=receipt.total,
        date=make_timestamp(receipt.date),
        timezone=receipt.timezone,
        allocations=[
          messages.ReceiptAllocation(
            bucket=allocation.bucket.guid.hex,
            amount=allocation.amount,
          )
          for allocation in receipt.allocations
        ],
        vendor_ref=receipt.vendor_ref,
        notes=receipt.notes,
        hash=receipt.hash,
      )
      receipt_messages.append(receipt_message)

    response = messages.ListReceiptsResponse(receipts=receipt_messages)
    bucket_desc = f"bucket {bucket_guid}" if bucket_guid else "unallocated receipts"
    logger.info(f"Returning {len(receipt_messages)} receipts for {bucket_desc}")
    return Response(message_to_json(response), content_type="application/json")
  except Bucket.DoesNotExist:
    logger.warning(f"Bucket not found: {bucket_guid}")
    return Response(json.dumps({"error": "Bucket not found"}), status=404, content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to list receipts: {e}")
    return Response(json.dumps({"error": "An unexpected error occurred"}), status=500, content_type="application/json")


# DeleteBucket RPC adapter
@app.route("/taxos.v1.TaxosApi/DeleteBucket", methods=["POST"])
@require_auth
def delete_bucket():
  logger.info("DeleteBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket_ref = BucketRef(request_data.get("guid", ""))
    success = DeleteBucket(ref=bucket_ref).execute()

    response = messages.DeleteBucketResponse(success=success)
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to delete bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/UpdateReceipt", methods=["POST"])
@require_auth
def update_receipt():
  logger.info("UpdateReceipt called via ConnectRPC")
  try:
    request_data = request.get_json() or {}

    allocations = _parse_allocations(request_data.get("allocations", []))

    receipt = UpdateReceipt(
      ref=get_text(request_data, "guid", "receipt_guid", "receiptGuid", default=""),
      vendor=get_text(request_data, "vendor", default=""),
      total=float(get_text(request_data, "total", default=0)),
      date=get_text(request_data, "date") or None,
      timezone=get_timezone(request_data),
      allocations=allocations,
      vendor_ref=get_text(request_data, "ref", "vendor_ref", "vendorRef", default=""),
      notes=get_text(request_data, "notes", default=""),
      hash=get_text(request_data, "hash", default=""),
    ).execute()

    receipt_message = Parse(domain_json.dumps(receipt), messages.Receipt())
    return Response(message_to_json(receipt_message), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to update receipt: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/DeleteReceipt", methods=["POST"])
@require_auth
def delete_receipt():
  logger.info("DeleteReceipt called via ConnectRPC")
  try:
    request_data = request.get_json()
    receipt_ref = ReceiptRef(get_text(request_data, "guid", "receipt_guid", "receiptGuid", default=""))
    success = DeleteReceipt(receipt_ref).execute()
    response_message = messages.DeleteReceiptResponse(success=success)
    return Response(message_to_json(response_message), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to delete receipt: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


def _get_upload_directory():
  """Get the uploads directory path."""
  return os.path.join(os.path.dirname(__file__), "..", "data", "uploads")


def _calculate_file_hash(file_data: bytes) -> str:
  """Calculate SHA-256 hash of file data."""
  return hashlib.sha256(file_data).hexdigest()


def _get_file_path(file_hash: str) -> str:
  """Get the file path for a given hash."""
  upload_dir = _get_upload_directory()
  return os.path.join(upload_dir, f"{file_hash}.zip")


def _file_exists(file_hash: str) -> bool:
  """Check if a file with the given hash already exists."""
  return os.path.exists(_get_file_path(file_hash))


def _save_file_as_zip(file_data: bytes, filename: str, file_hash: str) -> tuple[str, int]:
  """Save file data as a zip file with the hash as the filename."""
  zip_path = _get_file_path(file_hash)

  # Ensure upload directory exists
  os.makedirs(_get_upload_directory(), exist_ok=True)

  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr(filename, file_data)

  return zip_path, os.path.getsize(zip_path)


@app.route("/taxos.v1.TaxosApi/UploadReceiptFile", methods=["POST"])
@require_auth
def upload_receipt_file():
  logger.info("UploadReceiptFile called via ConnectRPC")
  try:
    request_data = request.get_json()
    # Handle both camelCase (from protobuf JS) and snake_case
    client_hash = request_data.get("fileHash") or request_data.get("file_hash", "")
    filename = request_data.get("filename", "")

    # Handle base64 encoded file data (typical for JSON APIs)
    import base64

    file_data_b64 = request_data.get("fileData") or request_data.get("file_data", "")

    if not client_hash:
      return Response(json.dumps({"error": "file_hash is required"}), status=400, content_type="application/json")

    if not filename:
      return Response(json.dumps({"error": "filename is required"}), status=400, content_type="application/json")

    # Check if file already exists
    if _file_exists(client_hash):
      logger.info(f"File with hash {client_hash} already exists, returning existing info")
      zip_path = _get_file_path(client_hash)
      file_size = os.path.getsize(zip_path)

      # Get upload timestamp from file modification time
      upload_timestamp = datetime.fromtimestamp(os.path.getmtime(zip_path), tz=timezone.utc)
      ts = Timestamp()
      ts.FromDatetime(upload_timestamp)

      file_info = messages.UploadReceiptFileInfo(
        file_hash=client_hash, filename=filename, file_path=zip_path, file_size=file_size, uploaded_at=ts
      )

      response_message = messages.UploadReceiptFileResponse(already_exists=True, file_info=file_info)
      return Response(message_to_json(response_message), content_type="application/json")

    # Decode file data
    if not file_data_b64:
      return Response(
        json.dumps({"error": "file_data is required for new uploads"}), status=400, content_type="application/json"
      )

    try:
      file_data = base64.b64decode(file_data_b64)
    except Exception as e:
      return Response(
        json.dumps({"error": f"Invalid base64 file_data: {e}"}), status=400, content_type="application/json"
      )

    # Validate hash
    calculated_hash = _calculate_file_hash(file_data)
    if calculated_hash != client_hash:
      logger.warning(f"Hash mismatch: client={client_hash}, calculated={calculated_hash}")
      return Response(json.dumps({"error": "File hash validation failed"}), status=400, content_type="application/json")

    # Save file as zip
    zip_path, file_size = _save_file_as_zip(file_data, filename, client_hash)
    logger.info(f"Saved file {filename} with hash {client_hash} as {zip_path}")

    # Create response
    upload_timestamp = datetime.now(timezone.utc)
    ts = Timestamp()
    ts.FromDatetime(upload_timestamp)

    file_info = messages.UploadReceiptFileInfo(
      file_hash=client_hash, filename=filename, file_path=zip_path, file_size=file_size, uploaded_at=ts
    )

    response_message = messages.UploadReceiptFileResponse(already_exists=False, file_info=file_info)
    return Response(message_to_json(response_message), content_type="application/json")

  except Exception as e:
    logger.error(f"Failed to upload file: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/DownloadReceiptFile", methods=["POST"])
@require_auth
def download_receipt_file():
  logger.info("DownloadReceiptFile called via ConnectRPC")
  try:
    request_data = request.get_json()
    # Handle both camelCase (from protobuf JS) and snake_case
    file_hash = request_data.get("fileHash") or request_data.get("file_hash", "")

    if not file_hash:
      return Response(json.dumps({"error": "file_hash is required"}), status=400, content_type="application/json")

    # Check if file exists
    if not _file_exists(file_hash):
      logger.warning(f"File with hash {file_hash} not found")
      return Response(json.dumps({"error": "File not found"}), status=404, content_type="application/json")

    # Read file from zip
    zip_path = _get_file_path(file_hash)
    with zipfile.ZipFile(zip_path, "r") as zipf:
      # Get the first (and should be only) file in the zip
      filenames = zipf.namelist()
      if not filenames:
        return Response(json.dumps({"error": "Zip file is empty"}), status=500, content_type="application/json")

      filename = filenames[0]
      file_data = zipf.read(filename)

    file_size = len(file_data)

    logger.info(f"Downloaded file {filename} with hash {file_hash} ({file_size} bytes)")
    response_message = messages.DownloadReceiptFileResponse(filename=filename, file_data=file_data, file_size=file_size)
    return Response(message_to_json(response_message), content_type="application/json")

  except Exception as e:
    logger.error(f"Failed to download file: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/Authenticate", methods=["POST"])
def authenticate():
  logger.info("Authenticate called via ConnectRPC")
  try:
    request_data = request.get_json() or {}
    token = request_data.get("token", "")
    if not token:
      return Response(json.dumps({"error": "Missing token"}), status=400, content_type="application/json")
    tenant = AuthenticateTenant(token).execute()
    response_message = messages.AuthenticateResponse()
    response_message.name = tenant.name
    return Response(message_to_json(response_message), content_type="application/json")
  except Exception as e:
    logger.warning(f"Authentication failed: {e}")
    return Response(json.dumps({"error": str(e)}), status=401, content_type="application/json")


if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  logger.info("Starting ConnectRPC HTTP server on port 50051...")
  app.run(host="0.0.0.0", port=50051, debug=True)
