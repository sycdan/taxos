from taxos.tenant.entity import Tenant
from taxos.tenant.load.query import LoadTenant
from taxos.tenant.tools import get_state_file
from taxos.tools import json


def handle(command: LoadTenant):
  guid = command.ref.guid
  state_file = get_state_file(guid)

  if state_file.exists():
    state = json.load(state_file)
    return Tenant(
      guid,
      state.get("name", guid),
      state.get("token_count", 0),
    )

  raise Tenant.DoesNotExist(guid)
