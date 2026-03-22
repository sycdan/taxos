import logging
import os

from taxos.context.tools import require_tenant
from taxos.tools import json
from taxos.vendor.entity import Vendor
from taxos.vendor.load.query import LoadVendor
from taxos.vendor.tools import get_state_file
from taxos.vendor.update.command import UpdateVendor

logger = logging.getLogger(__name__)


def handle(command: UpdateVendor) -> Vendor:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  vendor = LoadVendor(ref=command.ref).execute()

  vendor.name = command.name.strip()

  state_file = get_state_file(vendor.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)

  json.dump(vendor, state_file)

  return vendor
