import logging
import os

from taxos.context.tools import require_tenant
from taxos.index_unallocated_receipts.command import IndexUnallocatedReceipts
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.tools import get_unallocated_file
from taxos.tenant.tools import get_receipts_dir
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: IndexUnallocatedReceipts) -> list[Receipt]:
  tenant = require_tenant(command.tenant)

  logger.info(f"Indexing unallocated receipts for tenant {tenant.guid}")
  unallocated_receipts: list[Receipt] = []
  index: dict[str, set[str]] = {}  # month -> guids
  receipts_dir = get_receipts_dir(tenant.guid)
  unallocated_file = get_unallocated_file(tenant.guid)
  if unallocated_file.exists() and unallocated_file.stat().st_size > 0:
    logger.info(f"Loading existing unallocated receipts index for tenant {tenant.guid}")
    state = json.load(unallocated_file)
    index.update({k: set(v) for k, v in state.items()})

  if not receipts_dir.exists():
    logger.info(f"Creating receipts directory for tenant {tenant.guid}")
    os.makedirs(receipts_dir, exist_ok=True)

  content_dirs = []
  if command.receipt:
    try:
      receipt = command.receipt.hydrate()
      content_dirs.append(receipt.state_file.parent)
    except Receipt.DoesNotExist:
      pass
  else:
    content_dirs.extend(receipts_dir.iterdir())

  for receipt_dir in content_dirs:
    if not receipt_dir.is_dir():
      logger.debug(f"Skipping non-directory item: {receipt_dir}")
      continue

    if not (receipt := ReceiptRef(receipt_dir.name).hydrate()):
      logger.debug(f"Skipping receipt with missing or invalid state: {receipt_dir.name}")
      continue

    if receipt.is_unallocated:
      unallocated_receipts.append(receipt)
      month = receipt.date.strftime("%Y-%m")
      logger.debug(f"Indexing unallocated receipt for month {month}: {receipt.guid}")
      index.setdefault(month, set()).add(receipt.guid.hex)

  logger.info(f"Found {len(index)} unallocated receipts")

  with unallocated_file.open("w") as f:
    json.dump(index, f)

  return unallocated_receipts
