import json
import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.tenant.backup.command import DumpTenant

logger = logging.getLogger(__name__)


def handle(command: DumpTenant) -> dict:
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
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
    RETURN r, collect({bucket: b.guid, amount: a.amount}) AS allocations
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
        "vendor": node["vendor"],
        "total": node["total"],
        "date": node["date"],
        "timezone": node["timezone"],
        "allocations": allocs,
        "vendor_ref": node.get("reference", "") or "",
        "notes": node.get("notes", "") or "",
        "hash": node.get("hash", "") or "",
      }
    )

  data = {
    "buckets": [dict(r) for r in buckets],
    "vendors": [dict(r) for r in vendors],
    "receipts": receipts,
  }

  if command.path:
    with open(command.path, "w") as f:
      json.dump(data, f, indent=2)
    logger.info(f"Exported tenant {tenant.guid} to {command.path}")

  return data
