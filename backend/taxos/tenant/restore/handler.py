import json
import logging
import tempfile
import zipfile
from pathlib import Path
from uuid import UUID

from taxos.access.token.entity import AccessToken
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.allocation.entity import Allocation
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.entity import BucketRef
from taxos.context.entity import Context
from taxos.context.tools import with_context
from taxos.receipt.create.command import CreateReceipt
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import Tenant, TenantRef
from taxos.tenant.restore.command import RestoreTenant
from taxos.tools.guid import parse_guid
from taxos.vendor.find_or_create.command import FindOrCreateVendor

logger = logging.getLogger(__name__)


def _load_from_flat_dir(source: Path) -> tuple[UUID, dict]:
  """Read per-entity state.json files from a backup or tenant directory."""
  # Prefer tenant GUID from state.json; fall back to
  # deriving it from the directory name.
  state_file = source / "state.json"
  if state_file.exists():
    state = json.loads(state_file.read_text())
    if not (tenant_guid := parse_guid(state.get("guid", ""))):
      raise RuntimeError(f"Invalid tenant GUID in state.json: {state.get('guid')}")
  elif not (tenant_guid := parse_guid(source.name)):
    raise RuntimeError(f"Invalid tenant GUID in directory name: {source.name}")

  buckets = []
  buckets_dir = source / "buckets"
  if buckets_dir.exists():
    for bucket_state in sorted(buckets_dir.glob("*/state.json")):
      data = json.loads(bucket_state.read_text())
      buckets.append({"guid": data["guid"], "name": data["name"]})

  vendors = []
  vendors_dir = source / "vendors"
  if vendors_dir.exists():
    for vendor_state in sorted(vendors_dir.glob("*/state.json")):
      data = json.loads(vendor_state.read_text())
      vendors.append({"guid": data["guid"], "name": data["name"]})

  receipts = []
  receipts_dir = source / "receipts"
  if receipts_dir.exists():
    for receipt_state in sorted(receipts_dir.glob("*/state.json")):
      data = json.loads(receipt_state.read_text())

      receipts.append(
        {
          "guid": data["guid"],
          # Pass vendor GUID (new format) or name (legacy) directly to
          # CreateReceipt, which resolves both via LoadVendor / FindOrCreate.
          "vendor": data.get("vendor", ""),
          "total": data["total"],
          "date": data["date"],
          "timezone": data.get("timezone", "UTC"),
          "allocations": data.get("allocations", []),
          # Accept both vendor_ref (new/legacy) and reference (old export).
          "reference": data.get("vendor_ref", data.get("reference", "")) or "",
          "notes": data.get("notes", "") or "",
          "hash": data.get("hash", "") or "",
        }
      )

  return tenant_guid, {"buckets": buckets, "vendors": vendors, "receipts": receipts}


def handle(command: RestoreTenant) -> AccessToken:
  source = command.source

  if not source.exists():
    raise RuntimeError(f"Source not found: {source}")

  if source.suffix == ".zip":
    with tempfile.TemporaryDirectory() as tmp:
      with zipfile.ZipFile(source) as zf:
        zf.extractall(tmp)
      tenant_guid, data = _load_from_flat_dir(Path(tmp))
  elif source.is_dir():
    tenant_guid, data = _load_from_flat_dir(source)
  else:
    raise RuntimeError(f"Unsupported source format: {source}")

  if command.nuke:
    try:
      DeleteTenant(TenantRef(tenant_guid.hex)).execute()
    except Tenant.DoesNotExist:
      pass

  tenant = CreateTenant(command.name, tenant_guid).execute()

  @with_context(Context(tenant=tenant))
  def _restore():
    counts = {"buckets": 0, "vendors": 0, "receipts": 0}

    for b in data.get("buckets", []):
      if bucket_guid := parse_guid(b["guid"]):
        CreateBucket(name=b["name"], guid=bucket_guid).execute()
        counts["buckets"] += 1

    for v in data.get("vendors", []):
      if vendor_guid := parse_guid(v["guid"]):
        FindOrCreateVendor(name=v["name"], guid=vendor_guid).execute()
        counts["vendors"] += 1

    for r in data.get("receipts", []):
      if receipt_guid := parse_guid(r["guid"]):
        allocations = set()
        for alloc in r.get("allocations", []):
          if alloc_bucket_guid := parse_guid(alloc["bucket"]):
            allocations.add(
              Allocation(
                bucket=BucketRef(alloc_bucket_guid.hex),
                amount=alloc["amount"],
              )
            )
        CreateReceipt(
          vendor=r["vendor"],
          total=float(r["total"]),
          date=r["date"],
          timezone=r.get("timezone", "UTC"),
          allocations=allocations,
          reference=r["reference"],
          notes=r["notes"],
          hash=r["hash"],
          guid=receipt_guid,
        ).execute()
        counts["receipts"] += 1
    return counts

  counts = _restore()
  logger.info(
    f"Restored {tenant} ({tenant.guid}): "
    f"{counts['buckets']} buckets, {counts['vendors']} vendors, {counts['receipts']} receipts"
  )

  return GenerateAccessToken(tenant=tenant).execute()
