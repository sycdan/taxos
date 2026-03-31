import json
import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.tenant.backup.command import BackupTenant

logger = logging.getLogger(__name__)


def handle(command: BackupTenant) -> dict:
  tenant = require_tenant()

  buckets = db.query(
    "MATCH (b:Bucket) RETURN b.guid AS guid, b.name AS name ORDER BY b.name",
    database=tenant.db_name,
  )

  vendors = db.query(
    "MATCH (v:Vendor) RETURN v.guid AS guid, v.name AS name ORDER BY v.name",
    database=tenant.db_name,
  )

  receipt_records = db.query(
    """
    MATCH (r:Receipt)
    OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
    OPTIONAL MATCH (vf:Vendor {name_lower: toLower(r.vendor)})
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
    RETURN
      r,
      coalesce(v.name, vf.name, r.vendor, "") AS vendor,
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
        "vendor": record["vendor"],
        "total": node["total"],
        "date": node["date"],
        "timezone": node["timezone"],
        "allocations": allocs,
        "reference": node.get("reference", "") or "",
        "notes": node.get("notes", "") or "",
        "hash": node.get("hash", "") or "",
      }
    )

  data = {
    "tenant_guid": tenant.guid.hex,
    "buckets": [dict(r) for r in buckets],
    "vendors": [dict(r) for r in vendors],
    "receipts": receipts,
  }

  if command.path:
    with open(command.path, "w") as f:
      json.dump(data, f, indent=2)
    logger.info(f"Backed up tenant {tenant.guid} to {command.path}")

  return data
