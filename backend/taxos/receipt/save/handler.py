import os

from taxos.context.tools import require_tenant
from taxos.index_unallocated_receipts.command import IndexUnallocatedReceipts
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import json


def handle(command: SaveReceipt):
  tenant = require_tenant()
  receipt = command.receipt
  state_file = get_state_file(receipt.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)
  with state_file.open("w") as f:
    json.dump(receipt, f)
  IndexUnallocatedReceipts(tenant, receipt.guid).execute()
  return receipt
