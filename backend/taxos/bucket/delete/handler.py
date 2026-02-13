import logging
import shutil

from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.tools import get_state_file
from taxos.context.tools import require_bucket, require_tenant
from taxos.receipt.repo.load.command import LoadReceiptRepo

logger = logging.getLogger(__name__)


def handle(command: DeleteBucket):
  logger.debug(f"{command=}")
  tenant = require_tenant()
  bucket = require_bucket(command.ref)
  try:
    state_file = get_state_file(bucket.guid, tenant.guid)
    content_dir = state_file.parent
    if content_dir.exists():
      shutil.rmtree(content_dir)
      LoadReceiptRepo(force_rebuild=True).execute()
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
