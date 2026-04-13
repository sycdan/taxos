import json
import logging
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from taxos import BACKUPS_DIR, db
from taxos.context.tools import require_tenant
from taxos.tenant.backup.command import BackupTenant
from taxos.tenant.entity import Tenant
from taxos.receipt.load.handler import _read_file_attachments
from taxos.tenant.tools import get_files_dir

logger = logging.getLogger(__name__)


def _write_state(path: Path, data: dict) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(data, indent=2))


def _write_flat_dir(
  dest: Path,
  tenant: Tenant,
  buckets: list[dict],
  vendors: list[dict],
  receipts: list[dict],
) -> None:
  """Write the backup as a flat-directory of state.json files."""
  _write_state(
    dest / "state.json",
    {"guid": str(tenant.guid), "name": tenant.name},
  )

  for b in buckets:
    guid_hex = b["guid"].replace("-", "")
    _write_state(dest / "buckets" / guid_hex / "state.json", b)

  for v in vendors:
    guid_hex = v["guid"].replace("-", "")
    _write_state(dest / "vendors" / guid_hex / "state.json", v)

  for r in receipts:
    guid_hex = r["guid"].replace("-", "")
    _write_state(dest / "receipts" / guid_hex / "state.json", r)


def _copy_files(dest: Path, tenant: Tenant) -> None:
  """Copy tenant file attachments into the backup directory."""
  src = get_files_dir(tenant.guid)
  if not src.exists():
    return
  dest_files = dest / "files"
  dest_files.mkdir(parents=True, exist_ok=True)
  for f in src.iterdir():
    shutil.copy2(f, dest_files / f.name)


def handle(command: BackupTenant) -> Path:
  tenant = require_tenant()

  buckets = [
    dict(r)
    for r in db.query(
      "MATCH (b:Bucket) RETURN b.guid AS guid, b.name AS name ORDER BY b.name",
      database=tenant.db_name,
    )
  ]

  vendors = [
    dict(r)
    for r in db.query(
      "MATCH (v:Vendor) RETURN v.guid AS guid, v.name AS name ORDER BY v.name",
      database=tenant.db_name,
    )
  ]

  receipt_records = db.query(
    """
    MATCH (r:Receipt)
    OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
    OPTIONAL MATCH (vf:Vendor {name_lower: toLower(r.vendor)})
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
    RETURN
      r,
      coalesce(v.guid, vf.guid, "") AS vendor_guid,
      collect({bucket: b.guid, amount: a.amount}) AS allocations
    ORDER BY r.date
    """,
    database=tenant.db_name,
  )

  receipts = []
  for record in receipt_records:
    node = record["r"]
    allocs = [
      {"bucket": a["bucket"], "amount": a["amount"]}
      for a in record["allocations"]
      if a["bucket"] is not None
    ]
    receipts.append(
      {
        "guid": node["guid"],
        "vendor": record["vendor_guid"],
        "total": node["total"],
        "date": node["date"],
        "timezone": node["timezone"],
        "allocations": allocs,
        "vendor_ref": node.get("reference", "") or "",
        "notes": node.get("notes", "") or "",
        "file_attachments": _read_file_attachments(node),
      }
    )

  # Determine destination
  if command.path:
    dest = Path(command.path)
  else:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    filename = f"{tenant.name}_{timestamp}"
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUPS_DIR / (f"{filename}.zip" if command.zip else filename)

  if command.zip:
    with tempfile.TemporaryDirectory() as tmp:
      tmp_dir = Path(tmp)
      _write_flat_dir(tmp_dir, tenant, buckets, vendors, receipts)
      if command.include_files:
        _copy_files(tmp_dir, tenant)
      with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in tmp_dir.rglob("*"):
          zf.write(file, file.relative_to(tmp_dir))
  else:
    dest.mkdir(parents=True, exist_ok=True)
    _write_flat_dir(dest, tenant, buckets, vendors, receipts)
    if command.include_files:
      _copy_files(dest, tenant)

  logger.info(f"Backed up tenant {tenant.guid} to {dest}")
  return dest
