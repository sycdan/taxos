import os

from taxos.context.tools import require_tenant
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.tools import get_state_file
from taxos.tenant.unallocated_receipt.repo.update.query import UpdateUnallocatedReceiptRepo
from taxos.tools import json


def handle(command: SaveReceipt):
  tenant = require_tenant()
  receipt = command.receipt
  state_file = get_state_file(receipt.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)
  with state_file.open("w") as f:
    json.dump(receipt, f)
  UpdateUnallocatedReceiptRepo(receipt).execute()
  return receipt
