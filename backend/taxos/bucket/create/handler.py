import logging
import os

from taxos.bucket.create.command import CreateBucket
from taxos.bucket.entity import Bucket
from taxos.bucket.tools import get_state_file
from taxos.context.tools import require_tenant
from taxos.tools import guid, json

logger = logging.getLogger(__name__)


def handle(command: CreateBucket) -> Bucket:
  logger.debug(f"{command=}")
  tenant = require_tenant()

  bucket = Bucket(guid.uuid7(), command.name)

  state_file = get_state_file(bucket.guid, tenant.guid)
  if state_file.exists() and state_file.stat().st_size > 0:
    raise RuntimeError(f"Bucket {bucket.name} already exists.")

  os.makedirs(state_file.parent, exist_ok=True)

  json.dump(bucket, state_file)

  return bucket
