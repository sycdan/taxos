import logging
import os

from taxos.context.tools import require_tenant
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import guid
from taxos.tools.time import parse_datetime

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  receipt_guid = guid.uuid7()

  state_file = get_state_file(receipt_guid, tenant.guid)
  if state_file.exists() and state_file.stat().st_size > 0:
    raise RuntimeError(f"Receipt {receipt_guid} already exists.")

  receipt = Receipt(
    receipt_guid,
    vendor=command.vendor,
    total=command.total,
    date=parse_datetime(command.date, command.timezone),
    timezone=command.timezone,
    allocations=command.allocations or [],
    vendor_ref=command.ref,
    notes=command.notes,
    hash=command.hash,
  )


  return SaveReceipt(receipt).execute()