import logging

from taxos.context.tools import require_receipt
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.receipt.repo.save.command import SaveReceiptRepo
from taxos.receipt.repo.update.command import UpdateReceiptRepo

logger = logging.getLogger(__name__)


def handle(command: UpdateReceiptRepo) -> bool:
  """Returns True if the repo was updated, False otherwise."""
  logger.debug(f"{command=}")
  try:
    receipt = require_receipt(command.receipt)
  except Receipt.DoesNotExist:
    logger.warning(f"Receipt not found for repo update: {command.receipt}")
    return False

  try:
    repo: ReceiptRepo = LoadReceiptRepo().execute()
    if command.remove:
      repo.remove(receipt)
    else:
      repo.add(receipt)
    SaveReceiptRepo(repo).execute()
    return True
  except Exception as e:
    logger.error(f"Failed to update receipt repo: {e}")
  return False
