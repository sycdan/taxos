import logging
import shutil

from taxos.context.tools import require_tenant
from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.entity import Receipt, require_receipt
from taxos.receipt.repo.update.command import UpdateReceiptRepo
from taxos.receipt.tools import get_state_file

logger = logging.getLogger(__name__)


def handle(command: DeleteReceipt):
  logger.debug(f"{command=}")
  tenant = require_tenant()

  try:
    receipt = require_receipt(command.ref)
  except Receipt.DoesNotExist:
    logger.warning(f"Receipt not found for deletion: {command.ref}")
    return False

  UpdateReceiptRepo(receipt, remove=True).execute()
  receipt_guid = command.ref.guid
  state_file = get_state_file(receipt_guid, tenant.guid)
  content_dir = state_file.parent
  if content_dir.exists():
    shutil.rmtree(content_dir)
    return True
  return False
