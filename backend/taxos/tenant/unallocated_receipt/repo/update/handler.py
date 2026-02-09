import logging
import os
from datetime import date
from uuid import UUID

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.receipt.tools import get_unallocated_file
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tenant.unallocated_receipt.repo.entity import UnallocatedReceiptRepo
from taxos.tenant.unallocated_receipt.repo.load.query import LoadUnallocatedReceiptRepo
from taxos.tenant.unallocated_receipt.repo.update.query import UpdateUnallocatedReceiptRepo
from taxos.tools import json

logger = logging.getLogger(__name__)


def save_repo(repo: UnallocatedReceiptRepo):
  tenant = require_tenant()
  unallocated_file = get_unallocated_file(tenant.guid)
  os.makedirs(unallocated_file.parent, exist_ok=True)
  state = {}

  for month, unallocated_receipts in repo.index_by_month.items():
    month_key = month.strftime("%Y-%m")
    state.setdefault(month_key, []).extend([ur.receipt.guid.hex for ur in unallocated_receipts])

  with unallocated_file.open("w") as f:
    json.dump(state, f)


def handle(query: UpdateUnallocatedReceiptRepo) -> bool:
  """Returns True if the receipt is unallocated and was added to the repo, False otherwise."""
  repo: UnallocatedReceiptRepo = LoadUnallocatedReceiptRepo().execute()
  receipt = query.receipt.hydrate()
  added = False

  if unallocated_receipt := CheckUnallocatedReceipt(receipt).execute():
    logger.info(f"Receipt is unallocated, adding to unallocated repo: {receipt.guid}")
    repo.add(unallocated_receipt)
    added = True
  else:
    logger.info(f"Receipt is fully allocated, removing from unallocated repo if present: {receipt.guid}")
    repo.remove(receipt)

  save_repo(repo)
  return added
