import logging
from datetime import datetime

from taxos.context.tools import require_tenant
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.save.command import SaveReceipt
from taxos.tools.guid import parse_guid
from taxos.vendor.entity import VendorRef
from taxos.vendor.find_or_create.command import FindOrCreateVendor
from taxos.vendor.load.query import LoadVendor

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
  logger.debug(f"{command=}")
  require_tenant()

  # Accept either a vendor GUID (preferred) or name for backward compatibility.
  vendor = None
  if command.vendor:
    if vendor_guid := parse_guid(command.vendor):
      vendor = LoadVendor(ref=VendorRef(vendor_guid.hex)).execute()
    else:
      logger.debug(f"Vendor '{command.vendor}' is not a valid GUID, treating as name.")
      vendor = FindOrCreateVendor(command.vendor).execute()
      logger.debug(f"Vendor: {vendor.name} ({vendor.guid})")
  else:
    raise RuntimeError("Vendor is required to create a receipt.")

  receipt = Receipt(
    command.guid,
    vendor=vendor.name,
    total=command.total,
    date=command.date,
    timezone=command.timezone,
    allocations=command.allocations,
    vendor_ref=command.vendor_ref,
    notes=command.notes,
    hash=command.hash,
  )

  return SaveReceipt(receipt).execute()
