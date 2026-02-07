import json
import logging
from datetime import datetime
from uuid import UUID

from taxos.list_unallocated_receipts.query import ListUnallocatedReceipts
from taxos.receipt.entity import Receipt
from taxos.receipt.tools import get_state_file
from taxos.tenant.tools import get_receipts_dir
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def handle(query: ListUnallocatedReceipts, tenant_guid):
  logger.info(f"Handling {query}")
  unallocated_receipts: list[Receipt] = []
  receipts_dir = get_receipts_dir(tenant_guid)

  if not receipts_dir.exists():
    logger.info(f"No receipts directory found for tenant {tenant_guid}")
    return unallocated_receipts

  for receipt_dir in receipts_dir.iterdir():
    if not receipt_dir.is_dir():
      logger.debug(f"Skipping non-directory item: {receipt_dir}")
      continue

    receipt_guid = parse_guid(receipt_dir.name)
    if not receipt_guid:
      logger.debug(f"Skipping invalid GUID directory: {receipt_dir}")
      continue

    state_file = get_state_file(tenant_guid, receipt_guid)
    if not state_file.exists():
      logger.debug(f"No state file found for receipt {receipt_guid}")
      continue

    try:
      state_text = state_file.read_text().strip()
      if not state_text:
        logger.debug(f"Empty state file for receipt {receipt_guid}")
        continue

      receipt_data = json.loads(state_text)
      receipt = Receipt(
        guid=UUID(receipt_data["guid"]),
        vendor=receipt_data["vendor"],
        total=receipt_data["total"],
        date=receipt_data["date"],
        timezone=receipt_data["timezone"],
        tenant_guid=UUID(receipt_data["tenant_guid"]),
        allocations=receipt_data.get("allocations", []),
        ref=receipt_data.get("ref"),
        notes=receipt_data.get("notes"),
        hash=receipt_data.get("hash"),
      )

      if receipt.is_unallocated:
        if query.start_date or query.end_date:
          receipt_date = datetime.fromisoformat(receipt.date.replace("Z", "+00:00"))
          if query.start_date and receipt_date < query.start_date:
            continue
          if query.end_date and receipt_date > query.end_date:
            continue

        unallocated_receipts.append(receipt)
        logger.debug(f"Found unallocated receipt: {receipt_guid}")

    except (json.JSONDecodeError, KeyError, ValueError) as e:
      logger.warning(f"Error loading receipt {receipt_guid}: {e}")
      continue

  unallocated_receipts.sort(key=lambda r: r.date, reverse=True)
  logger.info(f"Found {len(unallocated_receipts)} unallocated receipts")
  return unallocated_receipts
