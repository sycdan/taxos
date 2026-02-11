import logging

from taxos.bucket.entity import Bucket
from taxos.context.tools import require_bucket, require_receipt, require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.query import LoadReceiptRepo
from taxos.receipt.tools import get_repo_file
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tools import json
from taxos.tools.time import parse_datetime

logger = logging.getLogger(__name__)


def handle(query: LoadReceiptRepo) -> ReceiptRepo:
  logger.debug(f"{query=}")
  assert not isinstance(query.start_date, str), "start_date should be a datetime, not a string"
  assert not isinstance(query.end_date, str), "end_date should be a datetime, not a string"
  assert not isinstance(query.bucket, str), "bucket should be a BucketRef, not a string"
  repo = ReceiptRepo()
  tenant = require_tenant()

  if query.bucket:
    bucket = require_bucket(query.bucket)
  else:
    bucket = None

  def should_include(receipt: Receipt) -> bool:
    logger.debug(f"Checking if receipt {receipt.guid} should be included for bucket {bucket}")
    if not bucket and not query.unallocated_only:
      return True
    if bucket:
      has_allocation = any(a.bucket.guid == bucket.guid for a in receipt.allocations)
      logger.debug(f"Receipt {receipt.guid} has allocation to bucket {bucket.guid}: {has_allocation}")
      return has_allocation
    elif query.unallocated_only and CheckUnallocatedReceipt(receipt).execute():
      return True
    return False

  repo_file = get_repo_file(tenant.guid)
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
      if should_include(receipt):
        repo.add(receipt)

  logger.info(f"Found {len(repo.receipts)} receipts")

  return repo
