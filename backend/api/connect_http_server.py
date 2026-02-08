import json
import logging
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, Response, request
from flask_cors import CORS
from google.protobuf.json_format import MessageToDict
from google.protobuf.timestamp_pb2 import Timestamp
from taxos.access.authenticate_tenant.command import AuthenticateTenant
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.update.command import UpdateBucket
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.list_buckets.query import ListBuckets
from taxos.receipt.create.command import CreateReceipt
from taxos.tenant.unallocated_receipts.list.query import ListUnallocatedReceipts

from api.v1 import taxos_service_pb2 as models

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


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


def _parse_allocations(values: list[dict]) -> list[dict]:
  allocations = []
  for item in values or []:
    if not isinstance(item, dict):
      continue
    bucket_guid = item.get("bucket_guid") or item.get("bucketGuid") or ""
    if not bucket_guid:
      continue
    amount = float(item.get("amount", 0))
    allocations.append({"bucket_guid": bucket_guid, "amount": amount})
  return allocations


@app.route("/taxos.v1.TaxosApi/ListBuckets", methods=["POST"])
@require_auth
def list_buckets():
  logger.info("ListBuckets called via ConnectRPC")
  try:
    repo = ListBuckets().execute()
    buckets = [
      models.BucketSummary(
        bucket=models.Bucket(
          guid=str(bucket.guid),
          name=bucket.name,
        )
      )
      for bucket in repo.index.values()
    ]

    response = models.ListBucketsResponse(buckets=buckets)
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    logger.info(f"Returning {len(buckets)} buckets")
    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to list buckets: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/CreateBucket", methods=["POST"])
@require_auth
def create_bucket():
  logger.info("CreateBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket = CreateBucket(request_data.get("name", "")).execute()

    response = models.Bucket(
      guid=str(bucket.guid),
      name=bucket.name,
    )
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to create bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/CreateReceipt", methods=["POST"])
@require_auth
def create_receipt():
  logger.info("CreateReceipt called via ConnectRPC")
  try:
    request_data = request.get_json() or {}
    date_value = request_data.get("date")
    date = _parse_timestamp(date_value)
    allocations = _parse_allocations(request_data.get("allocations", []))

    receipt = CreateReceipt(
      vendor=request_data.get("vendor", ""),
      total=float(request_data.get("total", 0)),
      date=date.isoformat(),
      timezone=request_data.get("timezone", ""),
      allocations=allocations,
      ref=request_data.get("ref") or "",
      notes=request_data.get("notes") or "",
      hash=request_data.get("hash") or "",
    ).execute()

    response_date = _parse_timestamp(receipt.date)
    ts = Timestamp()
    ts.FromDatetime(response_date)

    response = models.Receipt(
      guid=str(receipt.guid),
      vendor=receipt.vendor,
      date=ts,
      timezone=receipt.timezone,
      total=receipt.total,
      allocations=[
        models.ReceiptAllocation(
          bucket_guid=a.get("bucket_guid", ""),
          amount=float(a.get("amount", 0)),
        )
        for a in receipt.allocations
      ],
      ref=receipt.vendor_ref or "",
      notes=receipt.notes or "",
      hash=receipt.hash or "",
    )
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
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

    response = models.Bucket(
      guid=str(bucket.guid),
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

    response = models.Bucket(
      guid=str(bucket.guid),
      name=bucket.name,
    )
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to update bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


@app.route("/taxos.v1.TaxosApi/ListUnallocatedReceipts", methods=["POST"])
@require_auth
def list_unallocated_receipts():
  logger.info("ListUnallocatedReceipts called via ConnectRPC")
  try:
    request_data = request.get_json() or {}

    # Parse date filters from request
    start_date = None
    end_date = None
    if start_date_value := request_data.get("start_date"):
      start_date = _parse_timestamp(start_date_value)
    if end_date_value := request_data.get("end_date"):
      end_date = _parse_timestamp(end_date_value)

    receipts = ListUnallocatedReceipts(start_date=start_date, end_date=end_date).execute()

    # Convert receipts to protobuf format
    receipt_messages = []
    for receipt in receipts:
      # Convert date to timestamp
      response_date = _parse_timestamp(receipt.date)
      ts = Timestamp()
      ts.FromDatetime(response_date)

      receipt_message = models.Receipt(
        guid=str(receipt.guid),
        vendor=receipt.vendor,
        date=ts,
        timezone=receipt.timezone,
        total=receipt.total,
        allocations=[
          models.ReceiptAllocation(
            bucket_guid=a.get("bucket_guid", ""),
            amount=float(a.get("amount", 0)),
          )
          for a in receipt.allocations
        ],
        ref=receipt.vendor_ref or "",
        notes=receipt.notes or "",
        hash=receipt.hash or "",
      )
      receipt_messages.append(receipt_message)

    response = models.ListUnallocatedReceiptsResponse(receipts=receipt_messages)
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    logger.info(f"Returning {len(receipt_messages)} unallocated receipts")
    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to list unallocated receipts: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


# DeleteBucket RPC adapter
@app.route("/taxos.v1.TaxosApi/DeleteBucket", methods=["POST"])
@require_auth
def delete_bucket():
  logger.info("DeleteBucket called via ConnectRPC")
  try:
    request_data = request.get_json()
    bucket_ref = BucketRef(request_data.get("guid", ""))
    success = DeleteBucket(ref=bucket_ref).execute()

    response = models.DeleteBucketResponse(success=success)
    response_dict = MessageToDict(response, preserving_proto_field_name=True)

    return Response(json.dumps(response_dict), content_type="application/json")
  except Exception as e:
    logger.error(f"Failed to delete bucket: {e}")
    return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  logger.info("Starting ConnectRPC HTTP server on port 50051...")
  app.run(host="0.0.0.0", port=50051, debug=True)
