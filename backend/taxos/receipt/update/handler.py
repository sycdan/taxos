import logging
from datetime import datetime

from taxos.context.tools import require_receipt, require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.update.command import UpdateReceiptRepo
from taxos.receipt.tools import get_state_file
from taxos.receipt.update.command import UpdateReceipt
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: UpdateReceipt) -> Receipt:
  assert isinstance(command.date, datetime), "Date must be parsed."
  logger.debug(f"{command=}")
  tenant = require_tenant()
  receipt = require_receipt(command.ref)

  receipt.vendor = command.vendor
  receipt.total = command.total
  receipt.allocations = command.allocations
  receipt.date = command.date
  receipt.timezone = command.timezone
  receipt.vendor_ref = command.vendor_ref
  receipt.notes = command.notes
  receipt.hash = command.hash

  state_file = get_state_file(receipt.guid, tenant.guid)
  json.dump(receipt, state_file)

  UpdateReceiptRepo(receipt).execute()

  return receipt
