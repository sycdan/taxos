import hashlib
import logging
import os
from uuid import UUID

from taxos.access.token.entity import AccessToken
from taxos.access.token.generate.command import GenerateAccessToken
from taxos.access.token.tools import get_token_file
from taxos.tenant.load.query import LoadTenant
from taxos.tools import json as json_utils

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
  logger.info(f"Handling {command}")

  tenant = LoadTenant(ref=command.tenant_ref).execute()
  new_token_count = tenant.token_count + 1

  token_hash = generate_token_hash(tenant.guid, new_token_count)

  access_token = AccessToken(key=token_hash, tenant_ref=command.tenant_ref)
  token_file = get_token_file(token_hash)

  os.makedirs(token_file.parent, exist_ok=True)
  token_file.write_text(json_utils.dumps({"tenant_ref": command.tenant_ref.guid.hex}, indent=2))

  tenant.token_count = new_token_count
  tenant.state_file.write_text(json_utils.dumps(tenant, indent=2))

  if new_token_count > 1:
    delete_old_token(tenant.guid, new_token_count)

  logger.info(f"Generated new access token for tenant {command.tenant_ref.guid}")
  return access_token
