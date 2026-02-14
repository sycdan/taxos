from taxos.context.tools import require_tenant
from taxos.tools import json
from taxos.vendor.entity import Vendor
from taxos.vendor.load.query import LoadVendor
from taxos.vendor.tools import get_state_file


def handle(query: LoadVendor) -> Vendor:
  tenant = require_tenant()
  guid = query.ref.guid

  state_file = get_state_file(guid, tenant.guid)
  if state_file.exists():
    state = json.load(state_file)
    return Vendor(guid, state.get("name", str(guid)))

  raise Vendor.DoesNotExist(guid)
