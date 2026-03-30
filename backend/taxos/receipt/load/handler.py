import logging

from taxos import db
from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.load.query import LoadReceipt
from taxos.vendor.entity import Vendor

logger = logging.getLogger(__name__)


def _record_to_receipt(record) -> Receipt:
  r = record["r"]
  vendor_guid = record["vendor_guid"]
  vendor_name = record["vendor_name"]
  if not vendor_guid or not vendor_name:
    raise RuntimeError(f"Receipt {r['guid']} is missing vendor linkage.")
  allocations = set()
  for alloc in record["allocations"]:
    if alloc["bucket"] is not None:
      allocations.add(Allocation(BucketRef(alloc["bucket"]), alloc["amount"]))
  return Receipt(
    guid=r["guid"],
    vendor=Vendor(vendor_guid, vendor_name),
    total=r["total"],
    date=r["date"],
    timezone=r["timezone"],
    allocations=allocations,
    reference=r.get("reference", ""),
    notes=r.get("notes", ""),
    hash=r.get("hash", ""),
  )


def handle(query: LoadReceipt) -> Receipt:
  logger.debug(f"{query=}")
  tenant = require_tenant()
  guid = query.ref.guid
  records = db.query(
    """
    MATCH (r:Receipt {guid: $guid})
    OPTIONAL MATCH (r)-[:FROM_VENDOR]->(v:Vendor)
    OPTIONAL MATCH (vf:Vendor {name_lower: toLower(r.vendor)})
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
    RETURN
      r,
      coalesce(v.guid, vf.guid) AS vendor_guid,
      coalesce(v.name, vf.name, r.vendor) AS vendor_name,
      collect({bucket: b.guid, amount: a.amount}) AS allocations
    """,
    {"guid": guid.hex},
    database=tenant.db_name,
  )
  if not records:
    raise Receipt.DoesNotExist(guid)
  return _record_to_receipt(records[0])
