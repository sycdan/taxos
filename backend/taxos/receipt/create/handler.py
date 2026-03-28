import logging
from datetime import datetime

from taxos.context.tools import require_tenant
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.save.command import SaveReceipt
from taxos.tools import guid
from taxos.vendor.find_or_create.command import FindOrCreateVendor

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
  logger.debug(f"{command=}")
  require_tenant()

  # Find or create vendor to enable typeahead
  if command.vendor:
    vendor = FindOrCreateVendor(command.vendor).execute()
    logger.debug(f"Vendor: {vendor.name} ({vendor.guid})")

  receipt = Receipt(
    command.guid,
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
