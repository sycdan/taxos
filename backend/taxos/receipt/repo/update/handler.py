import logging
import os

from taxos.context.tools import require_tenant, require_receipt
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.query import LoadReceiptRepo
from taxos.receipt.repo.update.command import UpdateReceiptRepo
from taxos.receipt.tools import get_repo_file
from taxos.tools import json

logger = logging.getLogger(__name__)


def save_repo(repo: ReceiptRepo):
  tenant = require_tenant()
  repo_file = get_repo_file(tenant.guid)
  os.makedirs(repo_file.parent, exist_ok=True)
  state = {}

  for month, receipts in repo.index_by_month.items():
    month = month.strftime("%Y-%m")
    state.setdefault(month, []).extend([r.guid.hex for r in receipts])

  json.safe_dump(state, repo_file)


def handle(command: UpdateReceiptRepo) -> bool:
  """Returns True if the repo was updated, False otherwise."""
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
    save_repo(repo)
    return True
  except Exception as e:
    logger.error(f"Failed to update receipt repo: {e}")
  return False
