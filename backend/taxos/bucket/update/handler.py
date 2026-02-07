import logging
import os

from taxos.bucket.tools import get_state_file
from taxos.bucket.update.command import UpdateBucket
from taxos.context.tools import require_tenant
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: UpdateBucket):
  logger.debug(f"{command=}")
  tenant = require_tenant()
  bucket = command.ref.hydrate()

  bucket.name = command.name

  state_file = get_state_file(bucket.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)
  with state_file.open("w") as f:
    json.dump(bucket, f)
  return bucket
