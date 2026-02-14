import hashlib
import json
import logging
import zipfile
from datetime import datetime, timezone
from functools import wraps
from typing import TypeVar
from uuid import uuid4

from flask import Flask, Response, request
from flask_cors import CORS
from google.protobuf.json_format import MessageToDict, ParseDict, ParseError
from google.protobuf.message import Message
from google.protobuf.timestamp_pb2 import Timestamp
from taxos.access.authenticate_tenant.command import AuthenticateTenant
from taxos.allocation.entity import Allocation
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.update.command import UpdateBucket
from taxos.context.entity import Context
from taxos.context.tools import require_tenant, set_context
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.download_file import DownloadFile
from taxos.receipt.update.command import UpdateReceipt
from taxos.tenant.dashboard.get.query import GetDashboard
from taxos.tenant.list_receipts.query import ListReceipts
from taxos.tenant.tools import get_files_dir

from api.v1 import taxos_service_pb2 as messages

logger = logging.getLogger("api")

app = Flask(__name__)
CORS(app)
T = TypeVar("T", bound=Message)


def get_request_data() -> dict:
  data = request.get_json() or {}
  if not isinstance(data, dict):
    logger.warning("Request data is not a dict")
    return {}
  return data


def get_request_message(message_type: type[T], ignore_unknown_fields=False) -> T:
  """Hydrates a protobuf message from the current API request."""
  data = get_request_data()
  logger.debug("Hydrating %s from request data: %s", message_type.__name__, data)
  message = message_type()
  ParseDict(data, message, ignore_unknown_fields=ignore_unknown_fields)
  return message


def message_to_success_response(message: Message) -> Response:
  message_dict = MessageToDict(
    message,
    preserving_proto_field_name=False,  # frontend uses camelCase
    always_print_fields_with_no_presence=True,
  )
  text = json.dumps(message_dict)
  return Response(text, content_type="application/json")


def error_response(
  status: int = 500,
  message: str = "An unexpected error occurred",
  exception: Exception | None = None,
) -> Response:
  if exception:
    logger.error("Request to %s raised %s: %s", request.path, type(exception).__name__, exception)
  else:
    logger.warning("Request to %s failed %s: %s", request.path, status, message)
  return Response(json.dumps({"error": message}), status=status, content_type="application/json")


def make_timestamp(value: datetime) -> Timestamp:
  ts = Timestamp()
  ts.FromDatetime(value)
  return ts


def make_receipt_message(receipt) -> messages.Receipt:
  return messages.Receipt(
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
      return error_response(401, "Missing or invalid Authorization header")

    token_hash = auth_header[7:]  # Remove "Bearer " prefix

    try:
      tenant = AuthenticateTenant(token_hash).execute()
      context = Context(tenant=tenant)
      set_context(context)
      return f(*args, **kwargs)
    except Exception as e:
      logger.warning(f"Authentication failed: {e}")
      return error_response(401, "Invalid or expired access token")

  return decorated_function


def rpc_endpoint(request_message_type: type[T]):
  """Decorator for RPC endpoints to handle type boilerplate type conversions."""

  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      try:
        req = get_request_message(request_message_type, True)
        response_message = f(req, *args, **kwargs)
        if isinstance(response_message, Response):
          return response_message
        return message_to_success_response(response_message)
      except (ParseError, ValueError, TypeError) as e:
        return error_response(400, str(e))
      except FileNotFoundError as e:
        return error_response(404, str(e))
      except Exception as e:
        return error_response(exception=e)

    return decorated_function

  return decorator


def _parse_allocations(values: list[dict]) -> set:
  """Converts API allocation dicts to domain Allocation objects."""

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


@app.route("/taxos.v1.TaxosApi/GetDashboard", methods=["POST"])
@require_auth
@rpc_endpoint(messages.GetDashboardRequest)
def get_dashboard(req: messages.GetDashboardRequest):
  dashboard = GetDashboard(list(req.months)).execute()
  bucket_summaries = []
  for bs in dashboard.buckets:
    bucket_summaries.append(
      messages.BucketSummary(
        guid=bs.guid,
        name=bs.name,
        total_amount=bs.total_amount,
        receipt_count=bs.receipt_count,
      )
    )

  unallocated_receipt_messages = [make_receipt_message(r) for r in dashboard.unallocated]
  return messages.GetDashboardResponse(
    buckets=bucket_summaries,
    unallocated_receipts=unallocated_receipt_messages,
  )


@app.route("/taxos.v1.TaxosApi/CreateBucket", methods=["POST"])
@require_auth
@rpc_endpoint(messages.CreateBucketRequest)
def create_bucket(req: messages.CreateBucketRequest):
  bucket = CreateBucket(
    req.name or uuid4().hex[:8],
  ).execute()
  return messages.Bucket(
    guid=bucket.guid.hex,
    name=bucket.name,
  )


@app.route("/taxos.v1.TaxosApi/CreateReceipt", methods=["POST"])
@require_auth
@rpc_endpoint(messages.CreateReceiptRequest)
def create_receipt(req: messages.CreateReceiptRequest):
  allocations = _parse_allocations([MessageToDict(a) for a in req.allocations])

  receipt = CreateReceipt(
    vendor=req.vendor,
    total=req.total,
    date=req.date.ToDatetime(),
    timezone=req.timezone,
    allocations=allocations,
    vendor_ref=req.vendor_ref,
    notes=req.notes,
    hash=req.hash,
  ).execute()

  return make_receipt_message(receipt)


@app.route("/taxos.v1.TaxosApi/GetBucket", methods=["POST"])
@require_auth
@rpc_endpoint(messages.GetBucketRequest)
def get_bucket(req: messages.GetBucketRequest):
  bucket_ref = BucketRef(req.guid)
  bucket = LoadBucket(ref=bucket_ref).execute()

  return messages.Bucket(
    guid=bucket.guid.hex,
    name=bucket.name,
  )


@app.route("/taxos.v1.TaxosApi/UpdateBucket", methods=["POST"])
@require_auth
@rpc_endpoint(messages.UpdateBucketRequest)
def update_bucket(req: messages.UpdateBucketRequest):
  bucket_ref = BucketRef(req.guid)
  bucket = UpdateBucket(ref=bucket_ref, name=req.name).execute()

  return messages.Bucket(
    guid=bucket.guid.hex,
    name=bucket.name,
  )


@app.route("/taxos.v1.TaxosApi/ListReceipts", methods=["POST"])
@require_auth
@rpc_endpoint(messages.ListReceiptsRequest)
def list_receipts(req: messages.ListReceiptsRequest):
  months = list(req.months)
  receipts = ListReceipts(months=months, bucket=req.bucket).execute()
  receipt_messages = [make_receipt_message(r) for r in receipts]
  logger.info(f"Returning {len(receipt_messages)} receipts for bucket {req.bucket}")
  return messages.ListReceiptsResponse(receipts=receipt_messages)


@app.route("/taxos.v1.TaxosApi/DeleteBucket", methods=["POST"])
@require_auth
@rpc_endpoint(messages.DeleteBucketRequest)
def delete_bucket(req: messages.DeleteBucketRequest):
  success = DeleteBucket(ref=req.guid).execute()
  return messages.DeleteBucketResponse(success=success)


@app.route("/taxos.v1.TaxosApi/UpdateReceipt", methods=["POST"])
@require_auth
@rpc_endpoint(messages.UpdateReceiptRequest)
def update_receipt(req: messages.UpdateReceiptRequest):
  allocations = _parse_allocations([MessageToDict(a) for a in req.allocations])

  receipt = UpdateReceipt(
    ref=req.guid,
    vendor=req.vendor,
    total=req.total,
    date=req.date.ToDatetime(),
    timezone=req.timezone,
    allocations=allocations,
    vendor_ref=req.vendor_ref,
    notes=req.notes,
    hash=req.hash,
  ).execute()

  return make_receipt_message(receipt)


@app.route("/taxos.v1.TaxosApi/DeleteReceipt", methods=["POST"])
@require_auth
@rpc_endpoint(messages.DeleteReceiptRequest)
def delete_receipt(req: messages.DeleteReceiptRequest):
  success = DeleteReceipt(ref=req.guid).execute()
  return messages.DeleteReceiptResponse(success=success)


def _calculate_file_hash(file_data: bytes) -> str:
  """Calculate SHA-256 hash of file data."""
  return hashlib.sha256(file_data).hexdigest()


@app.route("/taxos.v1.TaxosApi/UploadReceiptFile", methods=["POST"])
@require_auth
@rpc_endpoint(messages.UploadReceiptFileRequest)
def upload_receipt_file(req: messages.UploadReceiptFileRequest):
  client_hash = req.file_hash
  filename = req.filename
  file_data = req.file_data

  if not client_hash:
    return Response(json.dumps({"error": "file_hash is required"}), status=400, content_type="application/json")

  if not filename:
    return Response(json.dumps({"error": "filename is required"}), status=400, content_type="application/json")

  # Get tenant's files directory
  tenant = require_tenant()
  files_dir = get_files_dir(tenant.guid)
  zip_path = files_dir / f"{client_hash}.zip"

  # Check if file already exists
  if zip_path.exists():
    logger.info(f"File with hash {client_hash} already exists, returning existing info")
    file_size = zip_path.stat().st_size

    # Get upload timestamp from file modification time
    upload_timestamp = datetime.fromtimestamp(zip_path.stat().st_mtime, tz=timezone.utc)
    ts = Timestamp()
    ts.FromDatetime(upload_timestamp)

    file_info = messages.UploadReceiptFileInfo(
      file_hash=client_hash, filename=filename, file_path=str(zip_path), file_size=file_size, uploaded_at=ts
    )

    return messages.UploadReceiptFileResponse(already_exists=True, file_info=file_info)

  # Decode file data is handled by protobuf already (bytes field)
  if not file_data:
    return Response(
      json.dumps({"error": "file_data is required for new uploads"}), status=400, content_type="application/json"
    )

  # Validate hash
  calculated_hash = _calculate_file_hash(file_data)
  if calculated_hash != client_hash:
    logger.warning(f"Hash mismatch: client={client_hash}, calculated={calculated_hash}")
    return Response(json.dumps({"error": "File hash validation failed"}), status=400, content_type="application/json")

  # Ensure files directory exists and save file as zip
  files_dir.mkdir(parents=True, exist_ok=True)
  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr(filename, file_data)

  file_size = zip_path.stat().st_size
  logger.info(f"Saved file {filename} with hash {client_hash} as {zip_path}")

  # Create response
  upload_timestamp = datetime.now(timezone.utc)
  ts = Timestamp()
  ts.FromDatetime(upload_timestamp)

  file_info = messages.UploadReceiptFileInfo(
    file_hash=client_hash, filename=filename, file_path=str(zip_path), file_size=file_size, uploaded_at=ts
  )

  return messages.UploadReceiptFileResponse(already_exists=False, file_info=file_info)


@app.route("/taxos.v1.TaxosApi/DownloadReceiptFile", methods=["POST"])
@require_auth
@rpc_endpoint(messages.DownloadReceiptFileRequest)
def download_receipt_file(req):
  result = DownloadFile(req.file_hash).execute()
  return messages.DownloadReceiptFileResponse(
    filename=result.filename, file_data=result.file_data, file_size=result.file_size
  )


@app.route("/taxos.v1.TaxosApi/Authenticate", methods=["POST"])
@rpc_endpoint(messages.AuthenticateRequest)
def authenticate(req: messages.AuthenticateRequest):
  token = req.token
  if not token:
    raise ValueError("Missing token")
  tenant = AuthenticateTenant(token).execute()
  return messages.AuthenticateResponse(name=tenant.name)


if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  logger.info("Starting ConnectRPC HTTP server on port 50051...")
  app.run(host="0.0.0.0", port=50051, debug=True)
