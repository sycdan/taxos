from taxos import db
from taxos.context.tools import require_tenant, require_vendor
from taxos.receipt.save.command import SaveReceipt


def handle(command: SaveReceipt):
  tenant = require_tenant()
  r = command.receipt
  vendor = require_vendor(r.vendor)

  if r.reference:
    conflict = db.query(
      """
      MATCH (v:Vendor {guid: $vendor_guid})<-[:FROM_VENDOR]-(other:Receipt)
      WHERE other.guid <> $receipt_guid AND other.reference = $reference
      RETURN count(other) AS cnt
      """,
      {
        "vendor_guid": vendor.guid.hex,
        "receipt_guid": r.guid.hex,
        "reference": r.reference,
      },
      database=tenant.db_name,
    )
    if (conflict[0]["cnt"] or 0) > 0:
      raise ValueError(
        f"Reference '{r.reference}' already exists for vendor {vendor.guid.hex}."
      )

  db.run(
    """
    MERGE (r:Receipt {guid: $guid})
    SET r.total = $total, r.date = $date, r.timezone = $timezone,
        r.notes = $notes, r.hash = $hash, r.reference = $reference
    REMOVE r.vendor
    """,
    {
      "guid": r.guid.hex,
      "total": r.total,
      "date": r.date.isoformat(),
      "timezone": r.timezone,
      "notes": r.notes or "",
      "hash": r.hash or "",
      "reference": r.reference or "",
    },
    database=tenant.db_name,
  )

  db.run(
    "MATCH (r:Receipt {guid: $receipt_guid})-[rel:FROM_VENDOR]->(:Vendor) DELETE rel",
    {"receipt_guid": r.guid.hex},
    database=tenant.db_name,
  )

  db.run(
    """
    MATCH (r:Receipt {guid: $receipt_guid})
    MATCH (v:Vendor {guid: $vendor_guid})
    MERGE (r)-[:FROM_VENDOR]->(v)
    """,
    {"receipt_guid": r.guid.hex, "vendor_guid": vendor.guid.hex},
    database=tenant.db_name,
  )

  # Remove stale allocation edges before re-writing (handles updates)
  db.run(
    "MATCH (r:Receipt {guid: $guid})-[a:ALLOCATED_TO]->() DELETE a",
    {"guid": r.guid.hex},
    database=tenant.db_name,
  )
  for alloc in r.allocations:
    db.run(
      """
      MATCH (r:Receipt {guid: $receipt_guid})
      MATCH (b:Bucket  {guid: $bucket_guid})
      CREATE (r)-[:ALLOCATED_TO {amount: $amount}]->(b)
      """,
      {
        "receipt_guid": r.guid.hex,
        "bucket_guid": alloc.bucket.guid.hex,
        "amount": alloc.amount,
      },
      database=tenant.db_name,
    )

  return r
