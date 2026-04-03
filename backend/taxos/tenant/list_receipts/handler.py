import logging
from uuid import UUID

from taxos import db
from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef, UnallocatedBucket
from taxos.concepts import UNSPECIFIED
from taxos.context.tools import require_bucket, require_tenant, require_vendor
from taxos.receipt.entity import Receipt
from taxos.receipt.load.handler import _read_file_attachments
from taxos.tenant.list_receipts.query import ListReceipts
from taxos.vendor.entity import Vendor

logger = logging.getLogger(__name__)

VENDOR_MATCH = """
OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
OPTIONAL MATCH (vf:Vendor {name_lower: toLower(r.vendor)})
"""

RETURN_RECEIPTS_WITH_ALLOCATIONS_A = """
OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b2:Bucket)
RETURN
  r,
  coalesce(v.guid, vf.guid) AS vendor_guid,
  coalesce(v.name, vf.name, r.vendor) AS vendor_name,
  collect({bucket: b2.guid, amount: a.amount}) AS allocations
ORDER BY r.date DESC
"""

RETURN_RECEIPTS_WITH_ALLOCATIONS_A2 = """
OPTIONAL MATCH (r)-[a2:ALLOCATED_TO]->(b2:Bucket)
RETURN
  r,
  coalesce(v.guid, vf.guid) AS vendor_guid,
  coalesce(v.name, vf.name, r.vendor) AS vendor_name,
  collect({bucket: b2.guid, amount: a2.amount}) AS allocations
ORDER BY r.date DESC
"""


def _where_clause(query: ListReceipts, has_vendor_filter: bool) -> str:
  clauses = []
  if query.months:
    clauses.append("substring(toString(r.date), 0, 7) IN $months")
  if has_vendor_filter:
    clauses.append(
      "EXISTS { MATCH (r)-[:FROM_VENDOR]->(:Vendor {guid: $vendor_guid}) }"
    )
  return f"WHERE {' AND '.join(clauses)}" if clauses else ""


def _to_receipts(records) -> list[Receipt]:
  receipts = []
  for record in records:
    node = record["r"]
    raw_vendor_guid = record["vendor_guid"]
    raw_vendor_name = record["vendor_name"]
    vendor_guid = raw_vendor_guid or str(UNSPECIFIED)
    vendor_name = raw_vendor_name or "Unknown Vendor"
    if not raw_vendor_guid or not raw_vendor_name:
      logger.warning(f"Receipt {node['guid']} is missing vendor linkage.")

    allocations = set()
    for alloc in record["allocations"]:
      if alloc["bucket"] is not None:
        allocations.add(Allocation(BucketRef(alloc["bucket"]), alloc["amount"]))

    receipts.append(
      Receipt(
        guid=node["guid"],
        vendor=Vendor(UUID(vendor_guid), vendor_name),
        total=node["total"],
        date=node["date"],
        timezone=node["timezone"],
        allocations=allocations,
        reference=node.get("reference", ""),
        notes=node.get("notes", ""),
        file_attachments=_read_file_attachments(node),
      )
    )
  return receipts


def handle(query: ListReceipts) -> list[Receipt]:
  logger.debug(f"Handling {query=}")
  tenant = require_tenant()
  if query.bucket is None:
    bucket = None
  elif isinstance(query.bucket, BucketRef):
    bucket = require_bucket(query.bucket.guid.hex)
  else:
    bucket = require_bucket(query.bucket)
  vendor = require_vendor(query.vendor) if query.vendor is not None else None

  params = {
    "months": query.months or [],
    "vendor_guid": vendor.guid.hex if vendor is not None else None,
  }
  where = _where_clause(query, has_vendor_filter=vendor is not None)

  if isinstance(bucket, UnallocatedBucket):
    records = db.query(
      f"""
      MATCH (r:Receipt)
      {where}
      {VENDOR_MATCH}
      OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(:Bucket)
      WITH r, v, vf, coalesce(sum(a.amount), 0) AS total_allocated
      WHERE r.total > total_allocated
      {RETURN_RECEIPTS_WITH_ALLOCATIONS_A2}
      """,
      params,
      database=tenant.db_name,
    )
  elif bucket is not None:
    records = db.query(
      f"""
      MATCH (b:Bucket {{guid: $bucket_guid}})<-[:ALLOCATED_TO]-(r:Receipt)
      {where}
      {VENDOR_MATCH}
      {RETURN_RECEIPTS_WITH_ALLOCATIONS_A}
      """,
      {
        **params,
        "bucket_guid": bucket.guid.hex,
      },
      database=tenant.db_name,
    )
  else:
    records = db.query(
      f"""
      MATCH (r:Receipt)
      {where}
      {VENDOR_MATCH}
      {RETURN_RECEIPTS_WITH_ALLOCATIONS_A}
      """,
      params,
      database=tenant.db_name,
    )
  return _to_receipts(records)
