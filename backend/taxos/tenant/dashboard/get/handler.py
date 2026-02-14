import logging

from taxos.receipt.entity import Receipt
from taxos.bucket.repo.load.query import LoadBucketRepo
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.tenant.dashboard.entity import BucketSummary, Dashboard
from taxos.tenant.dashboard.get.query import GetDashboard
from taxos.tenant.list_receipts.query import ListReceipts
from taxos.vendor.list.query import ListVendors

logger = logging.getLogger(__name__)


def handle(query: GetDashboard) -> Dashboard:
  logger.info(f"Generating dashboard for months: {query.months}")
  bucket_repo = LoadBucketRepo().execute()
  receipt_repo = LoadReceiptRepo().execute()

  bucket_summaries: list[BucketSummary] = []
  unallocated_receipts: list[Receipt] = []

  # Calculate summaries for each bucket
  for bucket in bucket_repo.index.values():
    receipts = ListReceipts(
      months=query.months,
      bucket=bucket,
      repo=receipt_repo,
    ).execute()

    total_amount = sum(sum(a.amount for a in r.allocations if a.bucket.guid == bucket.guid) for r in receipts)
    receipt_count = len(receipts)

    bucket_summaries.append(
      BucketSummary(
        guid=bucket.guid.hex,
        name=bucket.name,
        total_amount=total_amount,
        receipt_count=receipt_count,
      )
    )

  for month in query.months:
    for receipt in receipt_repo.iter_by_month(month):
      total_allocated = sum(a.amount for a in receipt.allocations)
      if receipt.total > total_allocated:
        unallocated_receipts.append(receipt)

  # Get all vendor names for typeahead
  vendors = ListVendors().execute()
  vendor_names = [vendor.name for vendor in vendors]

  return Dashboard(
    buckets=bucket_summaries,
    unallocated=unallocated_receipts,
    vendor_names=vendor_names,
  )
