import logging
from datetime import datetime

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.update.command import UpdateReceipt
from taxos.receipt.load.query import LoadReceipt

logger = logging.getLogger(__name__)


def handle(command: UpdateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
  logger.debug(f"{command=}")
  require_tenant()

  ref = command.ref if isinstance(command.ref, ReceiptRef) else ReceiptRef(str(command.ref.guid))
  receipt = LoadReceipt(ref=ref).execute()

  receipt.vendor = command.vendor
  receipt.total = command.total
  receipt.allocations = command.allocations
  receipt.date = command.date
  receipt.timezone = command.timezone
  receipt.vendor_ref = command.vendor_ref
  receipt.notes = command.notes
  receipt.hash = command.hash

  return SaveReceipt(receipt).execute()
