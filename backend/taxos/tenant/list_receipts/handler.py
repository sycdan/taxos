import logging

from taxos import db
from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_bucket, require_tenant
from taxos.concepts import UNALLOCATED_BUCKET_V1_SINGLETON
from taxos.receipt.entity import Receipt
from taxos.tenant.list_receipts.query import ListReceipts
from taxos.vendor.entity import Vendor

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
      OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
      OPTIONAL MATCH (vf:Vendor {{name_lower: toLower(r.vendor)}})
      OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(:Bucket)
      WITH r, coalesce(sum(a.amount), 0) AS total_allocated
      WHERE r.total > total_allocated
      OPTIONAL MATCH (r)-[a2:ALLOCATED_TO]->(b2:Bucket)
      RETURN
        r,
        coalesce(v.guid, vf.guid) AS vendor_guid,
        coalesce(v.name, vf.name, r.vendor) AS vendor_name,
        collect({{bucket: b2.guid, amount: a2.amount}}) AS allocations
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
      OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
      OPTIONAL MATCH (vf:Vendor {{name_lower: toLower(r.vendor)}})
      OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b2:Bucket)
      RETURN
        r,
        coalesce(v.guid, vf.guid) AS vendor_guid,
        coalesce(v.name, vf.name, r.vendor) AS vendor_name,
        collect({{bucket: b2.guid, amount: a.amount}}) AS allocations
      ORDER BY r.date DESC
      """,
      {"bucket_guid": bucket.guid.hex, "months": query.months or []},
      database=tenant.db_name,
    )

  receipts = []
  for record in records:
    node = record["r"]
    vendor_guid = record["vendor_guid"]
    vendor_name = record["vendor_name"]
    if not vendor_guid or not vendor_name:
      raise RuntimeError(f"Receipt {node['guid']} is missing vendor linkage.")
    allocations = set()
    for alloc in record["allocations"]:
      if alloc["bucket"] is not None:
        allocations.add(Allocation(BucketRef(alloc["bucket"]), alloc["amount"]))
    receipts.append(
      Receipt(
        guid=node["guid"],
        vendor=Vendor(vendor_guid, vendor_name),
        total=node["total"],
        date=node["date"],
        timezone=node["timezone"],
        allocations=allocations,
        reference=node.get("reference", ""),
        notes=node.get("notes", ""),
        hash=node.get("hash", ""),
      )
    )
  return receipts
