import logging
import os

from taxos.allocation.entity import Allocation
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt, require_receipt
from taxos.receipt.repo.update.command import UpdateReceiptRepo
from taxos.receipt.tools import get_state_file
from taxos.receipt.update.command import UpdateReceipt
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: UpdateReceipt) -> Receipt:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  receipt = require_receipt(command.ref)

  # Update receipt fields
  receipt.vendor = command.vendor
  receipt.total = command.total
  receipt.date = command.date
  receipt.timezone = command.timezone
  receipt.vendor_ref = command.vendor_ref
  receipt.notes = command.notes
  receipt.hash = command.hash

  # Update allocations - convert from dict format to Allocation objects
  receipt.allocations = {
    Allocation(bucket=a.get("bucket_guid", ""), amount=a.get("amount", 0)) for a in command.allocations
  }

  # Save to state file atomically to avoid race conditions
  state_file = get_state_file(receipt.guid, tenant.guid)
  os.makedirs(state_file.parent, exist_ok=True)
  temp_file = state_file.with_suffix(".tmp")
  with temp_file.open("w") as f:
    json.dump(receipt, f)
  temp_file.replace(state_file)

  # Update the receipt repo
  UpdateReceiptRepo(receipt).execute()

  return receipt
