import logging

from taxos.context.tools import require_bucket, require_receipt, require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.query import LoadReceiptRepo
from taxos.receipt.tools import get_repo_file
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(query: LoadReceiptRepo) -> ReceiptRepo:
  logger.debug(f"{query=}")

  repo = ReceiptRepo()
  tenant = require_tenant()

  bucket = None
  if query.bucket:
    bucket = require_bucket(query.bucket)

  def should_include(receipt: Receipt) -> bool:
    if not bucket and not query.unallocated_only:
      return True

    if bucket:
      has_allocation = any(a.bucket.guid == bucket.guid for a in receipt.allocations)
      logger.debug(f"Receipt {receipt.guid} has allocation to bucket {bucket.guid}: {has_allocation}")
      return has_allocation

    if query.unallocated_only:
      return CheckUnallocatedReceipt(receipt).execute() is not None

    return False

  repo_file = get_repo_file(tenant.guid)
  if not repo_file.exists():
    logger.info(f"No receipt index found for tenant {tenant.guid}")
    return repo

  state = json.load(repo_file)  # index is {month: [receipt_key, ...], ...}

  # Load only the specific months requested
  for month_key in query.months:
    if month_key not in state:
      continue

    for receipt_key in state[month_key]:
      try:
        receipt = require_receipt(receipt_key)
      except Receipt.DoesNotExist:
        logger.debug(f"Skipping missing receipt {receipt_key}")
        continue

      if should_include(receipt):
        repo.add(receipt)

  logger.info(f"Found {len(repo.receipts)} receipts")
  return repo
