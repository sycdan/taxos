import logging

from taxos.vendor.entity import Vendor
from taxos.vendor.list.query import ListVendors
from taxos.vendor.repo.load.query import LoadVendorRepo

logger = logging.getLogger(__name__)


def handle(query: ListVendors) -> list[Vendor]:
  logger.debug(f"{query=}")
  repo = LoadVendorRepo().execute()

  # Return vendors sorted by name
  vendors = sorted(repo.index.values(), key=lambda v: v.name.lower())
  return vendors
