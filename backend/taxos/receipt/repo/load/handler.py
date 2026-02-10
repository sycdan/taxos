import logging

from taxos.bucket.entity import Bucket
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, require_receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.query import LoadReceiptRepo
from taxos.receipt.tools import get_index_file
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tools import json
from taxos.tools.time import parse_datetime

logger = logging.getLogger(__name__)


def should_include(receipt: Receipt, bucket: Bucket | None = None) -> bool:
  if bucket:
    return any(a.bucket.guid == bucket.guid for a in receipt.allocations)
  elif CheckUnallocatedReceipt(receipt).execute():
    return True
  return False


def handle(query: LoadReceiptRepo) -> ReceiptRepo:
  assert not isinstance(query.start_date, str)
  assert not isinstance(query.end_date, str)
  assert not isinstance(query.timezone, str)
  assert not isinstance(query.bucket, str)
  repo = ReceiptRepo()
  tenant = require_tenant()

  if query.bucket:
    bucket = query.bucket.hydrate()
  else:
    bucket = None

  repo_file = get_index_file(tenant.guid)
  if not repo_file.exists():
    logger.info(f"No receipt index found for tenant {tenant.guid}")
    return repo

  state = json.load(repo_file)  # index is {month: [receipt_key, ...], ...}
  for month_key, receipt_keys in state.items():
    month = parse_datetime(month_key + "-01", query.timezone)
    if query.start_date and month < query.start_date:
      logger.debug(f"Skipping month {month_key} before {query.start_date}")
      continue
    if query.end_date and month > query.end_date:
      logger.debug(f"Skipping month {month_key} after {query.end_date}")
      continue

    for receipt_key in receipt_keys:
      try:
        receipt = require_receipt(receipt_key)
      except Receipt.DoesNotExist:
        logger.debug(f"Skipping missing receipt {receipt_key}")
        continue
      if should_include(receipt, bucket):
        repo.add(receipt)

  logger.info(f"Found {len(repo.receipts)} unallocated receipts")

  return repo
