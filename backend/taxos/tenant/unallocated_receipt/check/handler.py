import logging

from taxos.receipt.entity import Receipt, require_receipt
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tenant.unallocated_receipt.entity import UnallocatedReceipt

logger = logging.getLogger(__name__)


def calculate_unallocated_amount(receipt: Receipt) -> float:
  if not receipt.allocations:
    return receipt.total

  total_allocated = sum(a.amount for a in receipt.allocations)
  return receipt.total - total_allocated


def handle(command: CheckUnallocatedReceipt) -> UnallocatedReceipt | None:
  logger.debug(f"{command=}")
  receipt = require_receipt(command.receipt)

  unallocated_amount = calculate_unallocated_amount(receipt)
  if unallocated_amount:
    return UnallocatedReceipt(
      receipt,
      receipt.date.replace(day=1),
      unallocated_amount,
    )
