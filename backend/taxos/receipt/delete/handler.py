import logging
import shutil

from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.tools import get_state_file
from taxos.context.tools import require_tenant

logger = logging.getLogger(__name__)


def handle(command: DeleteReceipt):
  logger.debug(f"{command=}")
  tenant = require_tenant()
  try:
    receipt_guid = command.ref.guid
    state_file = get_state_file(receipt_guid, tenant.guid)
    content_dir = state_file.parent
    if content_dir.exists():
      shutil.rmtree(content_dir)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
