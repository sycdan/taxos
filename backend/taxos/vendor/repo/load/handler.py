import logging

from taxos.context.tools import require_tenant
from taxos.tools.guid import parse_guid
from taxos.vendor.entity import Vendor
from taxos.vendor.load.query import LoadVendor
from taxos.vendor.repo.entity import VendorRepo
from taxos.vendor.repo.load.query import LoadVendorRepo
from taxos.vendor.tools import get_vendors_dir

logger = logging.getLogger(__name__)


def handle(query: LoadVendorRepo) -> VendorRepo:
  logger.debug(f"{query=}")
  tenant = require_tenant()
  repo = VendorRepo()

  vendors_dir = get_vendors_dir(tenant.guid)
  if not vendors_dir.exists():
    logger.info(f"No vendors directory found for tenant {tenant.guid}")
    return repo

  for content_dir in vendors_dir.iterdir():
    if not content_dir.is_dir():
      logger.debug(f"Skipping non-directory item: {content_dir}")
      continue

    logger.debug(f"Checking dir: {content_dir}")
    if guid := parse_guid(content_dir.name):
      logger.info(f"Found vendor with GUID: {guid}")
      try:
        vendor = LoadVendor(guid.hex).execute()
        repo.add(vendor)
      except Vendor.DoesNotExist:
        logger.warning(f"Vendor with GUID {guid} does not exist, skipping.")

  return repo
