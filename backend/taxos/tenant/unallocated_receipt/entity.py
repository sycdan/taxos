from dataclasses import dataclass
from datetime import date

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class UnallocatedReceipt:
  receipt: Receipt | ReceiptRef
  month: date
  unallocated_amount: float

  def __hash__(self) -> int:
    return hash(self.receipt)
