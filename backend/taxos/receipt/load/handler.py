import logging

from taxos import db
from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.load.query import LoadReceipt

logger = logging.getLogger(__name__)


def _record_to_receipt(record) -> Receipt:
  r = record["r"]
  allocations = set()
  for alloc in record["allocations"]:
    if alloc["bucket"] is not None:
      allocations.add(Allocation(BucketRef(alloc["bucket"]), alloc["amount"]))
  return Receipt(
    guid=r["guid"],
    vendor=r["vendor"],
    total=r["total"],
    date=r["date"],
    timezone=r["timezone"],
    allocations=allocations,
    vendor_ref=r.get("reference", ""),
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
    OPTIONAL MATCH (r)-[a:ALLOCATED_TO]->(b:Bucket)
    RETURN r, collect({bucket: b.guid, amount: a.amount}) AS allocations
    """,
    {"guid": guid.hex},
    database=tenant.db_name,
  )
  if not records:
    raise Receipt.DoesNotExist(guid)
  return _record_to_receipt(records[0])
