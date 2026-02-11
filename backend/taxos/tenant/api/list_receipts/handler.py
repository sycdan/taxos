import logging

from taxos.context.tools import require_bucket
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.tenant.api.list_receipts.query import ListReceipts
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt

logger = logging.getLogger(__name__)


def handle(query: ListReceipts) -> list[Receipt]:
  repo: ReceiptRepo = LoadReceiptRepo().execute()
  receipts: list[Receipt] = []

  bucket = None  # include only unallocated by default
  if query.bucket:
    bucket = require_bucket(query.bucket)

  def should_include(receipt: Receipt) -> bool:
    if bucket:
      has_allocation = any(a.bucket.guid == bucket.guid for a in receipt.allocations)
      logger.debug(f"Receipt {receipt.guid} has allocation to bucket {bucket.guid}: {has_allocation}")
      return has_allocation
    return CheckUnallocatedReceipt(receipt).execute() is not None

  for month in query.months:
    for receipt in repo.iter_by_month(month):
      if should_include(receipt):
        receipts.append(receipt)
  return receipts
