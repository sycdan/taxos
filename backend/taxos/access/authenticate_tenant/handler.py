import json

from taxos.access.authenticate_tenant.command import AuthenticateTenant
from taxos.access.token.tools import get_token_file
from taxos.tenant.entity import Tenant, TenantRef
from taxos.tenant.load.query import LoadTenant


def handle(command: AuthenticateTenant) -> Tenant:
  token_file = get_token_file(command.token)

  if not token_file.exists():
    raise RuntimeError(f"Access token not found: {command.token}")

  token_data = json.loads(token_file.read_text())
  tenant_ref = TenantRef(token_data.get("tenant", ""))
  return tenant_ref.hydrate()
