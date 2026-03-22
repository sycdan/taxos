import logging

from taxos.context.tools import require_receipt
from taxos.receipt.entity import Receipt
from taxos.tenant.unallocated_receipt.check.command import CheckUnallocatedReceipt
from taxos.tenant.unallocated_receipt.entity import UnallocatedReceipt

logger = logging.getLogger(__name__)


def calculate_unallocated_amount(receipt: Receipt) -> float:
  if not receipt.allocations:
    return receipt.total

  total_allocated = sum(a.amount for a in receipt.allocations)
  return round(receipt.total - total_allocated, 2)


def handle(command: CheckUnallocatedReceipt) -> UnallocatedReceipt | None:
  logger.debug(f"{command=}")
  receipt = require_receipt(command.receipt)

  unallocated_amount = calculate_unallocated_amount(receipt)
  if unallocated_amount > 0:
    return UnallocatedReceipt(
      receipt,
      receipt.date.replace(day=1),
      unallocated_amount,
    )
