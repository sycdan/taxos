import logging

from taxos import db
from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_bucket, require_tenant
from taxos.receipt.entity import Receipt
from taxos.tenant.list_receipts.query import ListReceipts

logger = logging.getLogger(__name__)


def handle(query: ListReceipts) -> list[Receipt]:
  logger.debug(f"Handling {query=}")
  tenant = require_tenant()
  bucket = require_bucket(query.bucket)

  months_filter = "AND any(m IN $months WHERE r.date STARTS WITH m)" if query.months else ""

  records = db.query(
    f"""
    MATCH (b:Bucket {{guid: $bucket_guid}})<-[:ALLOCATED_TO]-(r:Receipt)
    {months_filter}
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b2:Bucket)
    RETURN r, collect({{bucket: b2.guid, amount: a.amount}}) AS allocations
    ORDER BY r.date DESC
    """,
    {"bucket_guid": bucket.guid.hex, "months": query.months or []},
    database=tenant.db_name,
  )

  receipts = []
  for record in records:
    node = record["r"]
    allocations = set()
    for alloc in record["allocations"]:
      if alloc["bucket"] is not None:
        allocations.add(Allocation(BucketRef(alloc["bucket"]), alloc["amount"]))
    receipts.append(Receipt(
      guid=node["guid"],
      vendor=node["vendor"],
      total=node["total"],
      date=node["date"],
      timezone=node["timezone"],
      allocations=allocations,
      vendor_ref=node.get("reference", ""),
      notes=node.get("notes", ""),
      hash=node.get("hash", ""),
    ))
  return receipts
