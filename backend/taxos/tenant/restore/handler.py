import json
import logging
from pathlib import Path
from typing import Optional
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


def _load_from_export_file(path: Path) -> tuple[Optional[UUID], dict]:
  with open(path) as f:
    data = json.load(f)
  # Extract tenant GUID if present, otherwise None (will generate a new one)
  tenant_guid = None
  if "tenant_guid" in data:
    if parsed_guid := parse_guid(data["tenant_guid"]):
      tenant_guid = parsed_guid
  return tenant_guid, data


def _load_from_flat_dir(source: Path) -> tuple[UUID, dict]:
  """Read the old per-entity state.json files from a tenant directory."""
  if not (tenant_guid := parse_guid(source.name)):
    raise RuntimeError(f"Invalid tenant GUID: {source.name}")

  buckets = []
  for state_file in sorted((source / "buckets").glob("*/state.json")):
    data = json.loads(state_file.read_text())
    buckets.append({"guid": data["guid"], "name": data["name"]})

  vendors = []
  for state_file in sorted((source / "vendors").glob("*/state.json")):
    data = json.loads(state_file.read_text())
    vendors.append({"guid": data["guid"], "name": data["name"]})

  receipts = []
  for state_file in sorted((source / "receipts").glob("*/state.json")):
    data = json.loads(state_file.read_text())
    receipts.append(
      {
        "guid": data["guid"],
        "vendor": data["vendor"],
        "total": data["total"],
        "date": data["date"],
        "timezone": data.get("timezone", "UTC"),
        "allocations": data.get("allocations", []),
        "reference": data.get("reference", data.get("vendor_ref", "")) or "",
        "notes": data.get("notes", "") or "",
        "hash": data.get("hash", "") or "",
      }
    )

  return tenant_guid, {"buckets": buckets, "vendors": vendors, "receipts": receipts}


def handle(command: RestoreTenant) -> AccessToken:
  source = command.source

  if not source.exists():
    raise RuntimeError(f"Source not found: {source}")

  if source.is_dir():
    tenant_guid, data = _load_from_flat_dir(source)
  else:
    tenant_guid, data = _load_from_export_file(source)
    if tenant_guid is None:
      from taxos.tools.guid import uuid7

      tenant_guid = uuid7()

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
