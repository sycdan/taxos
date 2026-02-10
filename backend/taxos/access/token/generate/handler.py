import hashlib
import logging
import os
from uuid import UUID

from taxos.access.token.entity import AccessToken
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.tools import get_token_file
from taxos.context.tools import require_tenant
from taxos.tools import json

logger = logging.getLogger(__name__)


def generate_token_hash(tenant_guid: UUID, token_count: int) -> str:
  token_string = f"{tenant_guid.hex}_{token_count}".encode("utf-8")
  return hashlib.sha256(token_string).hexdigest()


def delete_old_token(tenant_guid: UUID, new_token_count: int):
  old_token_hash = generate_token_hash(tenant_guid, new_token_count - 1)
  old_token_file = get_token_file(old_token_hash)
  if old_token_file.exists():
    old_token_file.unlink()
    logger.info(f"Deleted old access token: {old_token_hash}")


def handle(command: GenerateAccessToken) -> AccessToken:
  tenant = require_tenant(command.tenant)
  logger.info(f"Generating access token for {tenant}")

  new_token_count = tenant.token_count + 1
  token_hash = generate_token_hash(tenant.guid, new_token_count)
  token_file = get_token_file(token_hash)
  os.makedirs(token_file.parent, exist_ok=True)
  access_token = AccessToken(key=token_hash, tenant=tenant)
  tenant.token_count = new_token_count

  json.dump({"tenant": tenant.guid.hex}, token_file)
  json.dump(tenant, tenant.state_file)

  if new_token_count > 1:
    delete_old_token(tenant.guid, new_token_count)

  logger.info(f"Generated new access token for tenant {command.tenant.guid}")
  return access_token
