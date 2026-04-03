import base64
import hashlib
import logging
import zipfile
from functools import wraps
from pathlib import Path

from ariadne import (
  MutationType,
  ObjectType,
  QueryType,
  load_schema_from_path,
  make_executable_schema,
)
from ariadne.graphql import graphql_sync
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from taxos import db
from taxos.access.authenticate_tenant.command import AuthenticateTenant
from taxos.allocation.entity import Allocation
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.update.command import UpdateBucket
from taxos.context.entity import Context
from taxos.context.tools import require_tenant, set_context
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.load.query import LoadReceipt
from taxos.receipt.update.command import UpdateReceipt
from taxos.tenant.list_receipts.query import ListReceipts
from taxos.tenant.tools import get_files_dir
from taxos.tools.guid import parse_guid
from taxos.vendor.entity import Vendor, VendorRef
from taxos.vendor.find_or_create.command import FindOrCreateVendor
from taxos.vendor.list.query import ListVendors
from taxos.vendor.load.query import LoadVendor
from taxos.vendor.update.command import UpdateVendor

logger = logging.getLogger("api.graphql")

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


def require_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
      return Response(
        '{"errors":[{"message":"Missing or invalid Authorization header"}]}',
        status=401,
        content_type="application/json",
      )
    token_hash = auth_header[7:]
    try:
      tenant = AuthenticateTenant(token_hash).execute()
      set_context(Context(tenant=tenant))
      return f(*args, **kwargs)
    except Exception as e:
      logger.warning(f"Authentication failed: {e}")
      return Response(
        '{"errors":[{"message":"Invalid or expired access token"}]}',
        status=401,
        content_type="application/json",
      )

  return decorated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_allocations(items: list | None) -> set[Allocation]:
  allocations = set()
  for item in items or []:
    allocations.add(Allocation(BucketRef(item["bucketGuid"]), float(item["amount"])))
  return allocations


def _parse_file_attachments(items: list | None) -> dict[str, str] | None:
  if items is None:
    return None
  return {item["hash"]: item["name"] for item in items}


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------

query = QueryType()
mutation = MutationType()
vendor_type = ObjectType("Vendor")
bucket_type = ObjectType("Bucket")
receipt_type = ObjectType("Receipt")
allocation_type = ObjectType("Allocation")
file_attachment_type = ObjectType("FileAttachment")


# --- Query ---


@query.field("vendors")
def resolve_vendors(*_):
  return ListVendors().execute()


@query.field("vendor")
def resolve_vendor(*_, guid: str):
  try:
    return LoadVendor(ref=VendorRef(guid)).execute()
  except Vendor.DoesNotExist:
    return None


@query.field("buckets")
def resolve_buckets(*_):
  tenant = require_tenant()
  records = db.query(
    "MATCH (b:Bucket) RETURN b.guid AS guid, b.name AS name ORDER BY b.name",
    database=tenant.db_name,
  )
  from taxos.bucket.entity import Bucket

  return [Bucket(r["guid"], r["name"]) for r in records]


@query.field("bucket")
def resolve_bucket(*_, guid: str):
  try:
    return LoadBucket(ref=BucketRef(guid)).execute()
  except Bucket.DoesNotExist:
    return None


@query.field("receipts")
def resolve_receipts(*_, vendor=None, bucket=None, months=None):
  if vendor and not parse_guid(vendor):
    raise ValueError("vendor filter must be a valid GUID")
  if bucket and not parse_guid(bucket):
    raise ValueError("bucket filter must be a valid GUID")
  return ListReceipts(vendor=vendor, bucket=bucket, months=months or []).execute()


@query.field("receipt")
def resolve_receipt(*_, guid: str):
  try:
    return LoadReceipt(ref=guid).execute()  # type: ignore[arg-type]
  except Receipt.DoesNotExist:
    return None


# --- Mutation ---


@mutation.field("createBucket")
def resolve_create_bucket(*_, name: str):
  return CreateBucket(name=name).execute()


@mutation.field("updateBucket")
def resolve_update_bucket(*_, guid: str, name: str):
  return UpdateBucket(ref=BucketRef(guid), name=name).execute()


@mutation.field("deleteBucket")
def resolve_delete_bucket(*_, guid: str):
  return DeleteBucket(ref=guid).execute()


@mutation.field("createReceipt")
def resolve_create_receipt(*_, input: dict):
  return CreateReceipt(
    vendor=input["vendor"],
    total=input["total"],
    date=input["date"],
    timezone=input["timezone"],
    allocations=_parse_allocations(input.get("allocations")),
    notes=input.get("notes", ""),
    file_attachments=_parse_file_attachments(input.get("fileAttachments")) or {},
    reference=input.get("reference", ""),
  ).execute()


@mutation.field("updateReceipt")
def resolve_update_receipt(*_, guid: str, input: dict):
  return UpdateReceipt(
    ref=guid,
    vendor=input["vendor"],
    total=input["total"],
    date=input["date"],
    timezone=input["timezone"],
    allocations=_parse_allocations(input.get("allocations")),
    notes=input.get("notes", ""),
    file_attachments=_parse_file_attachments(input.get("fileAttachments")),
    reference=input.get("reference", ""),
  ).execute()


@mutation.field("deleteReceipt")
def resolve_delete_receipt(*_, guid: str):
  return DeleteReceipt(ref=guid).execute()


@mutation.field("updateVendor")
def resolve_update_vendor(*_, guid: str, name: str):
  return UpdateVendor(ref=VendorRef(guid), name=name).execute()


@mutation.field("upsertVendor")
def resolve_upsert_vendor(*_, name: str):
  return FindOrCreateVendor(name=name).execute()


@mutation.field("uploadReceiptFile")
def resolve_upload_receipt_file(*_, hash: str, filename: str, data: str):
  tenant = require_tenant()
  files_dir = get_files_dir(tenant.guid)
  zip_path = files_dir / f"{hash}.zip"

  if zip_path.exists():
    return {"hash": hash, "filename": filename, "alreadyExists": True}

  file_bytes = base64.b64decode(data)
  calculated_hash = hashlib.sha256(file_bytes).hexdigest()
  if calculated_hash != hash:
    raise ValueError("File hash validation failed")

  files_dir.mkdir(parents=True, exist_ok=True)
  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr(filename, file_bytes)

  return {"hash": hash, "filename": filename, "alreadyExists": False}


# --- Field resolvers ---


@vendor_type.field("guid")
def resolve_vendor_guid(vendor, *_):
  return vendor.guid.hex


@vendor_type.field("receipts")
def resolve_vendor_receipts(vendor, *_):
  return ListReceipts(vendor=vendor).execute()


@bucket_type.field("guid")
def resolve_bucket_guid(bucket, *_):
  return bucket.guid.hex


@bucket_type.field("totalAmount")
def resolve_bucket_total_amount(bucket, *_):
  tenant = require_tenant()
  records = db.query(
    """
    MATCH (b:Bucket {guid: $guid})
    OPTIONAL MATCH (b)<-[a:ALLOCATED_TO]-()
    RETURN sum(a.amount) AS total
    """,
    {"guid": bucket.guid.hex},
    database=tenant.db_name,
  )
  return records[0]["total"] or 0.0


@bucket_type.field("receiptCount")
def resolve_bucket_receipt_count(bucket, *_):
  tenant = require_tenant()
  records = db.query(
    """
    MATCH (b:Bucket {guid: $guid})
    OPTIONAL MATCH (b)<-[:ALLOCATED_TO]-(r:Receipt)
    RETURN count(DISTINCT r) AS cnt
    """,
    {"guid": bucket.guid.hex},
    database=tenant.db_name,
  )
  return records[0]["cnt"] or 0


@bucket_type.field("receipts")
def resolve_bucket_receipts(bucket: Bucket, *_, months=None):
  return ListReceipts(bucket=bucket, months=months or []).execute()


@receipt_type.field("guid")
def resolve_receipt_guid(receipt, *_):
  return receipt.guid.hex


@receipt_type.field("vendor")
def resolve_receipt_vendor(receipt, *_):
  vendor = receipt.vendor
  if isinstance(vendor, Vendor):
    return {"guid": vendor.guid.hex}
  return {"guid": vendor.guid.hex}


@receipt_type.field("date")
def resolve_receipt_date(receipt, *_):
  return receipt.date.isoformat()


@receipt_type.field("reference")
def resolve_receipt_reference(receipt, *_):
  return receipt.reference or ""


@receipt_type.field("notes")
def resolve_receipt_notes(receipt, *_):
  return receipt.notes or ""


@receipt_type.field("fileAttachments")
def resolve_receipt_file_attachments(receipt, *_):
  return [{"hash": h, "name": n} for h, n in (receipt.file_attachments or {}).items()]


@allocation_type.field("bucket")
def resolve_allocation_bucket(allocation, *_):
  ref = (
    allocation.bucket
    if isinstance(allocation.bucket, BucketRef)
    else BucketRef(allocation.bucket.guid.hex)
  )
  return LoadBucket(ref=ref).execute()


# --- Schema + app ---

schema = make_executable_schema(
  load_schema_from_path(Path(__file__).parent / "schema.graphql"),
  query,
  mutation,
  vendor_type,
  bucket_type,
  receipt_type,
  allocation_type,
  file_attachment_type,
)


@app.route("/files/<file_hash>", methods=["GET"])
@require_auth
def download_file_endpoint(file_hash):
  from taxos.receipt.download_file.command import DownloadFile

  try:
    result = DownloadFile(file_hash=file_hash).execute()
    return Response(
      result.file_data,
      content_type="application/octet-stream",
      headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
    )
  except FileNotFoundError:
    return Response(
      '{"errors":[{"message":"File not found"}]}',
      status=404,
      content_type="application/json",
    )


@app.route("/graphql", methods=["POST"])
@require_auth
def graphql_endpoint():
  data = request.get_json()
  success, result = graphql_sync(schema, data, context_value=request, debug=app.debug)
  return jsonify(result), 200 if success else 400


def main():
  logging.basicConfig(level=logging.DEBUG)
  logger.info("Starting GraphQL server on port 50052...")
  app.run(host="0.0.0.0", port=50052, debug=False, use_reloader=False)


if __name__ == "__main__":
  main()
