import logging
import os

from taxos.context.tools import require_tenant
from taxos.index_unallocated_receipts.command import IndexUnallocatedReceipts
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.tools import get_unallocated_file
from taxos.tenant.tools import get_receipts_dir
from taxos.tools import json

logger = logging.getLogger(__name__)


def _process(receipt_ref: ReceiptRef, unallocated_receipts: dict[str, set[str]]):
  try:
    receipt = receipt_ref.hydrate()
  except Receipt.DoesNotExist:
    logger.debug(f"Skipping receipt with missing or invalid state: {receipt_ref}")
    return
  if receipt.is_unallocated:
    month = receipt.date.strftime("%Y-%m")
    logger.debug(f"Indexing unallocated receipt for month {month}: {receipt.guid}")
    unallocated_receipts.setdefault(month, set()).add(receipt.guid.hex)


def handle(command: IndexUnallocatedReceipts) -> dict[str, set[str]]:
  unallocated_receipts: dict[str, set[str]] = {}  # month -> guids
  tenant = require_tenant(command.tenant)

  receipts_dir = get_receipts_dir(tenant.guid)
  if not receipts_dir.exists():
    logger.info(f"Creating receipts directory for tenant {tenant.guid}")
    os.makedirs(receipts_dir, exist_ok=True)

  logger.info(f"Indexing unallocated receipts for tenant {tenant.guid}")
  unallocated_file = get_unallocated_file(tenant.guid)
  if unallocated_file.exists() and unallocated_file.stat().st_size > 0:
    logger.info(f"Loading existing unallocated receipts index for tenant {tenant.guid}")
    state = json.load(unallocated_file)
    unallocated_receipts.update({k: set(v) for k, v in state.items()})

  if command.receipt:
    logger.info(f"Indexing single receipt {command.receipt} for tenant {tenant.guid}")
    _process(command.receipt, unallocated_receipts)
  else:
    for receipt_dir in receipts_dir.iterdir():
      if receipt_dir.is_dir():
        _process(ReceiptRef(receipt_dir.name), unallocated_receipts)

  logger.info(f"Found {len(unallocated_receipts)} unallocated receipts")

  with unallocated_file.open("w") as f:
    json.dump(unallocated_receipts, f)

  return unallocated_receipts
