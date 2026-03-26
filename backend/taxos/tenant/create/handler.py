import logging

from taxos import db
from taxos.tenant.create.command import CreateTenant
from taxos.tenant.entity import Tenant
from taxos.tenant.tools import get_state_file
from taxos.tools import guid, json

logger = logging.getLogger(__name__)


def handle(command: CreateTenant) -> Tenant:
  logger.info(f"Handling {command}")
  tenant = Tenant(guid=guid.uuid7(), name=command.name)

  state_file = get_state_file(tenant.guid)
  if state_file.exists() and state_file.read_text().strip():
    raise RuntimeError(f"Tenant {tenant.name} already exists.")

  json.dump(tenant, state_file)
  db.run(f"CREATE DATABASE {tenant.db_name} IF NOT EXISTS", database="system")
  return tenant
