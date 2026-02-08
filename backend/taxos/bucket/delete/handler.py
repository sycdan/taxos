import logging
import shutil

from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.tools import get_state_file
from taxos.context.tools import require_tenant

logger = logging.getLogger(__name__)


def handle(command: DeleteBucket):
  logger.debug(f"{command=}")
  tenant = require_tenant()
  try:
    bucket_guid = command.ref.guid
    state_file = get_state_file(bucket_guid, tenant.guid)
    content_dir = state_file.parent
    if content_dir.exists():
      shutil.rmtree(content_dir)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
