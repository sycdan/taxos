import logging
from datetime import datetime

from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_tenant
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import guid

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
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
    date=command.date,
    timezone=command.timezone,
    allocations=command.allocations,
    vendor_ref=command.vendor_ref,
    notes=command.notes,
    hash=command.hash,
  )

  return SaveReceipt(receipt).execute()
