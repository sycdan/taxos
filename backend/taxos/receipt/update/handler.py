import logging
from datetime import datetime

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.update.command import UpdateReceipt
from taxos.receipt.load.query import LoadReceipt
from taxos.vendor.entity import VendorRef
from taxos.vendor.find_or_create.command import FindOrCreateVendor
from taxos.vendor.load.query import LoadVendor

logger = logging.getLogger(__name__)


def handle(command: UpdateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
  logger.debug(f"{command=}")
  require_tenant()

  if isinstance(command.ref, ReceiptRef):
    ref = command.ref
  elif isinstance(command.ref, str):
    ref = ReceiptRef(command.ref)
  else:
    ref = ReceiptRef(str(command.ref.guid))
  receipt = LoadReceipt(ref=ref).execute()

  vendor = None
  if command.vendor:
    vendor_key = str(command.vendor).strip()
    try:
      vendor = LoadVendor(ref=VendorRef(vendor_key)).execute()
    except ValueError:
      vendor = FindOrCreateVendor(vendor_key).execute()

  receipt.vendor = vendor if vendor else receipt.vendor
  receipt.total = command.total
  receipt.allocations = command.allocations
  receipt.date = command.date
  receipt.timezone = command.timezone
  receipt.reference = command.reference
  receipt.notes = command.notes
  if command.file_attachments is not None:
    receipt.file_attachments = command.file_attachments

  return SaveReceipt(receipt).execute()
