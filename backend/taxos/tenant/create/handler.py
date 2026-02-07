import logging
import os

from taxos.tenant.create.command import CreateTenant
from taxos.tenant.entity import Tenant
from taxos.tools import guid, json

logger = logging.getLogger(__name__)


def handle(command: CreateTenant) -> Tenant:
  logger.info(f"Handling {command}")
  tenant = Tenant(guid=guid.uuid7(), name=command.name)

  if tenant.state_file.exists() and tenant.state_file.read_text().strip():
    raise RuntimeError(f"Tenant {tenant.name} already exists.")

  os.makedirs(tenant.content_dir, exist_ok=True)
  json.dump(tenant, tenant.state_file)
  return tenant
