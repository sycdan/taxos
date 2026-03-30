from taxos import db
from taxos.context.tools import require_tenant
from taxos.receipt.save.command import SaveReceipt
from taxos.tools.guid import parse_guid


def handle(command: SaveReceipt):
  tenant = require_tenant()
  r = command.receipt

  db.run(
    """
    MERGE (r:Receipt {guid: $guid})
    SET r.total = $total, r.date = $date, r.timezone = $timezone,
        r.vendor = $vendor, r.notes = $notes, r.hash = $hash,
        r.reference = $reference
    """,
    {
      "guid": r.guid.hex,
      "total": r.total,
      "date": r.date.isoformat(),
      "timezone": r.timezone,
      "vendor": r.vendor or "",
      "notes": r.notes or "",
      "hash": r.hash or "",
      "reference": r.vendor_ref or "",
    },
    database=tenant.db_name,
  )

  if r.vendor:
    db.run(
      "MATCH (r:Receipt {guid: $receipt_guid})-[rel:FROM_VENDOR]->(:Vendor) DELETE rel",
      {"receipt_guid": r.guid.hex},
      database=tenant.db_name,
    )

    vendor_guid = parse_guid(r.vendor_ref)
    if vendor_guid:
      db.run(
        """
        MATCH (r:Receipt {guid: $receipt_guid})
        MATCH (v:Vendor {guid: $vendor_guid})
        MERGE (r)-[:FROM_VENDOR]->(v)
        """,
        {"receipt_guid": r.guid.hex, "vendor_guid": vendor_guid.hex},
        database=tenant.db_name,
      )
    else:
      db.run(
        """
        MATCH (r:Receipt {guid: $receipt_guid})
        MATCH (v:Vendor {name_lower: toLower($vendor_name)})
        MERGE (r)-[:FROM_VENDOR]->(v)
        """,
        {"receipt_guid": r.guid.hex, "vendor_name": r.vendor},
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
