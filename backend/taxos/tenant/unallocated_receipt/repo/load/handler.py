import logging
from datetime import date
from pathlib import Path

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.load.query import LoadReceipt
from taxos.receipt.tools import get_index_file
from taxos.tenant.tools import get_receipts_dir
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tenant.unallocated_receipt.entity import UnallocatedReceipt
from taxos.tenant.unallocated_receipt.repo.entity import UnallocatedReceiptRepo
from taxos.tenant.unallocated_receipt.repo.load.query import LoadUnallocatedReceiptRepo
from taxos.tools import json

logger = logging.getLogger(__name__)


def _load_receipts_for_bucket(query: LoadUnallocatedReceiptRepo, repo: UnallocatedReceiptRepo, tenant_guid):
  """Load receipts allocated to a specific bucket by scanning all receipt directories."""
  receipts_dir = get_receipts_dir(tenant_guid)
  bucket_guid_str = str(query.bucket_guid)

  # Scan all receipt directories
  for receipt_dir in receipts_dir.iterdir():
    if not receipt_dir.is_dir():
      continue

    state_file = receipt_dir / "state.json"
    if not state_file.exists():
      continue

    try:
      # Load receipt
      receipt = LoadReceipt(ref=ReceiptRef(receipt_dir.name)).execute()

      # Check date range
      if query.start_date and receipt.date < query.start_date:
        continue
      if query.end_date and receipt.date > query.end_date:
        continue

      # Check if allocated to this bucket
      allocated_amount = 0
      for alloc_bucket_guid, amount in receipt.allocations:
        if alloc_bucket_guid == bucket_guid_str:
          allocated_amount += amount

      if allocated_amount > 0:
        # Add as "unallocated" receipt but with the allocated amount to this bucket
        month = receipt.date.replace(day=1)
        repo.add(UnallocatedReceipt(receipt, month, allocated_amount))
    except Exception as e:
      logger.debug(f"Skipping receipt {receipt_dir.name}: {e}")
      continue


def _load_unallocated_receipts(query: LoadUnallocatedReceiptRepo, repo: UnallocatedReceiptRepo, tenant_guid):
  """Load receipts that have unallocated amounts using the unallocated index."""
  unallocated_file = get_index_file(tenant_guid)
  if not unallocated_file.exists():
    logger.info(f"No unallocated receipts file found for tenant {tenant_guid}")
    return

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


def handle(query: LoadUnallocatedReceiptRepo) -> UnallocatedReceiptRepo:
  repo = UnallocatedReceiptRepo()
  tenant = require_tenant()

  if query.bucket_guid:
    # Load receipts allocated to specific bucket
    _load_receipts_for_bucket(query, repo, tenant.guid)
    logger.info(f"Found {len(repo.unallocated_receipts)} receipts for bucket {query.bucket_guid}")
  else:
    # Load unallocated receipts
    _load_unallocated_receipts(query, repo, tenant.guid)
    logger.info(f"Found {len(repo.unallocated_receipts)} unallocated receipts")

  return repo
