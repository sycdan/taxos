import json

from taxos.tenant.entity import Tenant
from taxos.tenant.load.query import LoadTenant
from taxos.tenant.tools import get_state_file


def handle(command: LoadTenant):
  guid = command.ref.guid
  state_file = get_state_file(guid)

  if not state_file.exists():
    raise RuntimeError(f"Tenant {guid} does not exist.")

  state = {}
  if text := state_file.read_text():
    state.update(json.loads(text))

  return Tenant(guid, state.get("name", guid), state.get("token_count", 0))
