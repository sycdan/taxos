import logging
import os

from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.tools import guid, json

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  logger.info(f"Handling {command}")
  receipt = Receipt(
    guid=guid.uuid7(),
    vendor=command.vendor,
    total=command.total,
    date=command.date,
    timezone=command.timezone,
    allocations=command.allocations or [],
    ref=command.ref,
    notes=command.notes,
    hash=command.hash,
  )

  if receipt.state_file.exists() and receipt.state_file.read_text().strip():
    raise RuntimeError(f"Receipt {receipt.guid} already exists.")

  os.makedirs(receipt.content_folder, exist_ok=True)
  receipt.state_file.write_text(json.dumps(receipt, indent=2))
  return receipt
