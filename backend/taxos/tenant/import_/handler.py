import json
import logging
from pathlib import Path

from taxos import db
from taxos.context.tools import require_tenant
from taxos.tenant.import_.command import ImportTenant

logger = logging.getLogger(__name__)


def _load_from_export_file(path: Path) -> dict:
  with open(path) as f:
    return json.load(f)


def _load_from_flat_dir(path: Path) -> dict:
  """Read the old per-entity state.json files from a tenant directory."""
  buckets = []
  for state_file in sorted((path / "buckets").glob("*/state.json")):
    data = json.loads(state_file.read_text())
    buckets.append({"guid": data["guid"], "name": data["name"]})

  vendors = []
  for state_file in sorted((path / "vendors").glob("*/state.json")):
    data = json.loads(state_file.read_text())
    vendors.append({"guid": data["guid"], "name": data["name"]})

  receipts = []
  for state_file in sorted((path / "receipts").glob("*/state.json")):
    data = json.loads(state_file.read_text())
    receipts.append({
      "guid": data["guid"],
      "vendor": data["vendor"],
      "total": data["total"],
      "date": data["date"],
      "timezone": data.get("timezone", "UTC"),
      "allocations": data.get("allocations", []),
      "vendor_ref": data.get("vendor_ref", "") or "",
      "notes": data.get("notes", "") or "",
      "hash": data.get("hash", "") or "",
    })

  return {"buckets": buckets, "vendors": vendors, "receipts": receipts}


def handle(command: ImportTenant) -> dict:
  tenant = require_tenant()
  source = Path(command.source)

  if source.is_dir():
    data = _load_from_flat_dir(source)
  else:
    data = _load_from_export_file(source)

  counts = {"buckets": 0, "vendors": 0, "receipts": 0}

  for b in data.get("buckets", []):
    db.run(
      "MERGE (b:Bucket {guid: $guid}) SET b.name = $name",
      {"guid": b["guid"], "name": b["name"]},
      database=tenant.db_name,
    )
    counts["buckets"] += 1

  for v in data.get("vendors", []):
    db.run(
      """
      MERGE (v:Vendor {guid: $guid})
      SET v.name = $name, v.name_lower = toLower($name)
      """,
      {"guid": v["guid"], "name": v["name"]},
      database=tenant.db_name,
    )
    counts["vendors"] += 1

  for r in data.get("receipts", []):
    db.run(
      """
      MERGE (r:Receipt {guid: $guid})
      SET r.vendor = $vendor,
          r.total = $total,
          r.date = $date,
          r.timezone = $timezone,
          r.reference = $vendor_ref,
          r.notes = $notes,
          r.hash = $hash
      """,
      {
        "guid": r["guid"],
        "vendor": r["vendor"],
        "total": float(r["total"]),
        "date": r["date"],
        "timezone": r.get("timezone", "UTC"),
        "vendor_ref": r.get("vendor_ref", "") or "",
        "notes": r.get("notes", "") or "",
        "hash": r.get("hash", "") or "",
      },
      database=tenant.db_name,
    )

    # Vendor edge
    db.run(
      """
      MATCH (r:Receipt {guid: $receipt_guid})
      MATCH (v:Vendor {name_lower: toLower($vendor_name)})
      MERGE (r)-[:FROM_VENDOR]->(v)
      """,
      {"receipt_guid": r["guid"], "vendor_name": r["vendor"]},
      database=tenant.db_name,
    )

    # Allocation edges — delete existing then recreate
    db.run(
      "MATCH (r:Receipt {guid: $guid})-[a:ALLOCATED_TO]->() DELETE a",
      {"guid": r["guid"]},
      database=tenant.db_name,
    )
    for alloc in r.get("allocations", []):
      db.run(
        """
        MATCH (r:Receipt {guid: $receipt_guid})
        MATCH (b:Bucket {guid: $bucket_guid})
        MERGE (r)-[:ALLOCATED_TO {amount: $amount}]->(b)
        """,
        {
          "receipt_guid": r["guid"],
          "bucket_guid": alloc["bucket"],
          "amount": float(alloc["amount"]),
        },
        database=tenant.db_name,
      )

    counts["receipts"] += 1

  logger.info(
    f"Imported into tenant {tenant.guid}: "
    f"{counts['buckets']} buckets, {counts['vendors']} vendors, {counts['receipts']} receipts"
  )
  return counts
