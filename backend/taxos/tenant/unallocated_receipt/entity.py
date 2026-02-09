from dataclasses import dataclass

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class UnallocatedReceipt:
  receipt: Receipt | ReceiptRef
  unallocated_amount: float

  def __hash__(self) -> int:
    return hash(self.receipt)
