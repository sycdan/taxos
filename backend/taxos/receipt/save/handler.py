from taxos.context.tools import require_tenant
from taxos.receipt.repo.update.command import UpdateReceiptRepo
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import json


def handle(command: SaveReceipt):
  tenant = require_tenant()
  receipt = command.receipt
  state_file = get_state_file(receipt.guid, tenant.guid)
  json.safe_dump(receipt, state_file)
  UpdateReceiptRepo(receipt).execute()
  return receipt
