import logging
import os

from taxos.context.tools import require_tenant
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.tools import get_state_file
from taxos.tools import guid, json
from taxos.tools.time import parse_datetime

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  tenant = require_tenant()
  logger.info(f"Handling {command}")
  receipt = Receipt(
    state_file=get_state_file(guid.uuid7(), tenant.guid),
    vendor=command.vendor,
    total=command.total,
    date=parse_datetime(command.date, command.timezone),
    timezone=command.timezone,
    allocations=command.allocations or [],
    vendor_ref=command.ref,
    notes=command.notes,
    hash=command.hash,
  )

  if receipt.state_file.exists() and receipt.state_file.stat().st_size > 0:
    raise RuntimeError(f"Receipt {receipt.guid} already exists.")

  os.makedirs(receipt.content_dir, exist_ok=True)
  json.dump(receipt, receipt.state_file)
  return receipt
