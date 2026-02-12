import logging

from taxos.context.tools import require_bucket
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.tenant.list_receipts.query import ListReceipts

logger = logging.getLogger(__name__)


def handle(query: ListReceipts) -> list[Receipt]:
  logger.debug(f"Handling {query=}")
  repo: ReceiptRepo = query.repo or LoadReceiptRepo().execute()
  receipts: list[Receipt] = []

  bucket = require_bucket(query.bucket)

  if not (month_keys := query.months):
    month_keys = list(repo.index_by_month.keys())

  def should_include(receipt: Receipt) -> bool:
    has_allocation = any(a.bucket.guid == bucket.guid for a in receipt.allocations)
    logger.debug(f"Receipt {receipt.guid} has allocation to bucket {bucket.guid}: {has_allocation}")
    return has_allocation

  for month in month_keys:
    for receipt in repo.iter_by_month(month):
      if should_include(receipt):
        receipts.append(receipt)
  return receipts
