import logging
import os

from taxos.context.tools import require_tenant
from taxos.tools import guid, json
from taxos.vendor.entity import Vendor
from taxos.vendor.find_or_create.command import FindOrCreateVendor
from taxos.vendor.repo.entity import VendorRepo
from taxos.vendor.repo.load.query import LoadVendorRepo
from taxos.vendor.tools import get_state_file

logger = logging.getLogger(__name__)


def handle(command: FindOrCreateVendor) -> Vendor:
  logger.debug(f"{command=}")
  tenant = require_tenant()

  # Load all vendors to check if one with this name already exists
  repo: VendorRepo = LoadVendorRepo().execute()

  # Search for existing vendor by name (case-insensitive)
  for vendor in repo.index.values():
    if vendor.name.lower() == command.name.lower():
      logger.info(f"Found existing vendor: {vendor.name} ({vendor.guid})")
      return vendor

  # No existing vendor found, create a new one
  logger.info(f"Creating new vendor: {command.name}")
  vendor = Vendor(guid.uuid7(), command.name)

  state_file = get_state_file(vendor.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)

  json.dump(vendor, state_file)

  return vendor
