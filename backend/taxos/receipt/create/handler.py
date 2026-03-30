import logging
from datetime import datetime

from taxos.context.tools import require_tenant
from taxos.receipt.create.command import CreateReceipt
from taxos.receipt.entity import Receipt
from taxos.receipt.save.command import SaveReceipt
from taxos.tools.guid import parse_guid
from taxos.vendor.entity import Vendor, VendorRef
from taxos.vendor.find_or_create.command import FindOrCreateVendor
from taxos.vendor.load.query import LoadVendor

logger = logging.getLogger(__name__)


def handle(command: CreateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
  logger.debug(f"{command=}")
  require_tenant()

  # Accept either a vendor GUID (preferred) or name for backward compatibility.
  vendor = None
  if isinstance(command.vendor, Vendor):
    vendor = command.vendor
  elif isinstance(command.vendor, VendorRef):
    vendor = LoadVendor(ref=command.vendor).execute()
  elif command.vendor:
    vendor_key = str(command.vendor).strip()
    if vendor_guid := parse_guid(vendor_key):
      vendor = LoadVendor(ref=VendorRef(vendor_guid.hex)).execute()
    else:
      logger.debug(f"Vendor '{vendor_key}' is not a valid GUID, treating as name.")
      vendor = FindOrCreateVendor(vendor_key).execute()
      logger.debug(f"Vendor: {vendor.name} ({vendor.guid})")
  else:
    raise RuntimeError("Vendor is required to create a receipt.")

  receipt = Receipt(
    command.guid,
    vendor=vendor,
    total=command.total,
    date=command.date,
    timezone=command.timezone,
    allocations=command.allocations,
    reference=command.reference,
    notes=command.notes,
    hash=command.hash,
  )

  return SaveReceipt(receipt).execute()
