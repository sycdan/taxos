import logging

from taxos import db
from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_bucket, require_tenant
from taxos.concepts import UNALLOCATED_BUCKET_V1_SINGLETON
from taxos.receipt.entity import Receipt
from taxos.tenant.list_receipts.query import ListReceipts

logger = logging.getLogger(__name__)


def handle(query: ListReceipts) -> list[Receipt]:
  logger.debug(f"Handling {query=}")
  tenant = require_tenant()
  bucket = require_bucket(query.bucket)

  months_filter = (
    "AND any(m IN $months WHERE r.date STARTS WITH m)" if query.months else ""
  )

  if query.bucket.guid == UNALLOCATED_BUCKET_V1_SINGLETON:
    months_clause = (
      "WHERE any(m IN $months WHERE r.date STARTS WITH m)" if query.months else ""
    )
    records = db.query(
      f"""
      MATCH (r:Receipt)
      {months_clause}
      OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(:Bucket)
      WITH r, coalesce(sum(a.amount), 0) AS total_allocated
      WHERE r.total > total_allocated
      OPTIONAL MATCH (r)-[a2:ALLOCATED_TO]->(b2:Bucket)
      RETURN r, collect({{bucket: b2.guid, amount: a2.amount}}) AS allocations
      ORDER BY r.date DESC
      """,
      {"months": query.months or []},
      database=tenant.db_name,
    )
  else:
    bucket = require_bucket(query.bucket)
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
    receipts.append(
      Receipt(
        guid=node["guid"],
        vendor=node["vendor"],
        total=node["total"],
        date=node["date"],
        timezone=node["timezone"],
        allocations=allocations,
        vendor_ref=node.get("reference", ""),
        notes=node.get("notes", ""),
        hash=node.get("hash", ""),
      )
    )
  return receipts
