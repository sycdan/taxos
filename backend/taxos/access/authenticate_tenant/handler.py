import json
import logging

from taxos.access.authenticate_tenant.command import AuthenticateTenant
from taxos.access.token.tools import get_token_file
from taxos.tenant.entity import Tenant, TenantRef

logger = logging.getLogger(__name__)


def handle(command: AuthenticateTenant) -> Tenant:
  token_file = get_token_file(command.token)

  if not token_file.exists():
    logger.warning(f"Access token file not found: {token_file}")
    raise RuntimeError(f"Access token not found: {command.token}")

  token_data = json.loads(token_file.read_text())
  tenant_ref = TenantRef(token_data.get("tenant", ""))
  if tenant := tenant_ref.hydrate():
    return tenant
  raise RuntimeError(f"Tenant not found for token: {command.token}")
