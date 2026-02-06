import json

from taxos.access.authenticate_tenant.command import Authenticate
from taxos.access.token.tools import get_token_file
from taxos.tenant.entity import Tenant, TenantRef
from taxos.tenant.load.query import LoadTenant


def handle(command: Authenticate) -> Tenant:
  token_file = get_token_file(command.access_token_key)

  if not token_file.exists():
    raise RuntimeError(f"Access token not found: {command.access_token_key}")

  token_data = json.loads(token_file.read_text())
  tenant_ref = TenantRef(token_data.get("tenant_ref", ""))
  return LoadTenant(ref=tenant_ref).execute()
