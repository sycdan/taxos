import logging
import os

from taxos.bucket.entity import Bucket
from taxos.bucket.tools import get_state_file
from taxos.bucket.update.command import UpdateBucket
from taxos.context.tools import require_tenant
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: UpdateBucket) -> Bucket:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  bucket = command.ref.hydrate()

  bucket.name = command.name

  state_file = get_state_file(bucket.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)
  
  # Write to temp file first, then atomically rename to avoid race conditions
  temp_file = state_file.with_suffix(".tmp")
  with temp_file.open("w") as f:
    json.dump(bucket, f)
  temp_file.replace(state_file)
  
  return bucket
