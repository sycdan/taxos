import logging
from datetime import datetime
from uuid import UUID

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.tools import get_state_file, get_unallocated_file
from taxos.tenant.tools import get_receipts_dir
from taxos.tenant.unallocated_receipts.list.query import ListUnallocatedReceipts
from taxos.tools import json
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def handle(query: ListUnallocatedReceipts):
  tenant = require_tenant()
  logger.info(f"Handling {query}")
  unallocated_receipts: list[Receipt] = []
  unallocated_file = get_unallocated_file(tenant.guid)
  if not unallocated_file.exists():
    logger.info(f"No unallocated receipts file found for tenant {tenant.guid}")
    return unallocated_receipts

  state = json.load(unallocated_file)
  for month_key, receipt_guids in state.items():
    month = datetime.strptime(month_key, "%Y-%m")
    if query.start_date and month < query.start_date:
      logger.debug(f"Skipping month {month_key} before {query.start_date}")
      continue
    if query.end_date and month > query.end_date:
      logger.debug(f"Skipping month {month_key} after {query.end_date}")
      continue
    for receipt_guid in receipt_guids:
      try:
        receipt = ReceiptRef(receipt_guid).hydrate()
      except Receipt.DoesNotExist:
        logger.debug(f"Skipping missing receipt {receipt_guid}")
        continue
      unallocated_receipts.append(receipt)

  unallocated_receipts.sort(key=lambda r: r.date, reverse=True)
  logger.info(f"Found {len(unallocated_receipts)} unallocated receipts")
  return unallocated_receipts
