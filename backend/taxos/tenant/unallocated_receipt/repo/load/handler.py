import logging
from datetime import date

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.tools import get_unallocated_file
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tenant.unallocated_receipt.repo.entity import UnallocatedReceiptRepo
from taxos.tenant.unallocated_receipt.repo.load.query import LoadUnallocatedReceiptRepo
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(query: LoadUnallocatedReceiptRepo) -> UnallocatedReceiptRepo:
  repo = UnallocatedReceiptRepo()
  tenant = require_tenant()

  unallocated_file = get_unallocated_file(tenant.guid)
  if not unallocated_file.exists():
    logger.info(f"No unallocated receipts file found for tenant {tenant.guid}")
    return repo

  state = json.load(unallocated_file)
  for month_key, receipt_keys in state.items():
    month = date.fromisoformat(month_key + "-01")
    if query.start_date and month < query.start_date:
      logger.debug(f"Skipping month {month_key} before {query.start_date}")
      continue
    if query.end_date and month > query.end_date:
      logger.debug(f"Skipping month {month_key} after {query.end_date}")
      continue
    for receipt_key in receipt_keys:
      try:
        if unallocated_receipt := CheckUnallocatedReceipt(receipt_key).execute():
          repo.add(unallocated_receipt)
      except Receipt.DoesNotExist:
        logger.debug(f"Skipping missing receipt {receipt_key}")
        continue

  logger.info(f"Found {len(repo.unallocated_receipts)} unallocated receipts")
  return repo
