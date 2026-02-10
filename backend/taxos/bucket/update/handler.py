import logging
import os

from taxos.bucket.entity import Bucket
from taxos.bucket.tools import get_state_file
from taxos.bucket.update.command import UpdateBucket
from taxos.context.tools import require_bucket, require_tenant
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: UpdateBucket) -> Bucket:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  bucket = require_bucket(command.ref)

  bucket.name = command.name

  state_file = get_state_file(bucket.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)

  json.dump(bucket, state_file)

  return bucket
