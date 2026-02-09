from dataclasses import dataclass
from typing import Union

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class CheckUnallocatedReceipt:
  """
  A receipt is considered unallocated if:
  - it has no allocations
  - the sum of its allocations is less than its total
  """

  receipt: Union[Receipt, ReceiptRef]

  def __post_init__(self):
    if not isinstance(self.receipt, (Receipt, ReceiptRef)):
      self.receipt = ReceiptRef(self.receipt)

  def execute(self):
    from taxos.tenant.unallocated_receipt.check.handler import handle

    return handle(self)
