from dataclasses import dataclass
from typing import Union

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class UpdateUnallocatedReceiptRepo:
  receipt: Union[Receipt, ReceiptRef]

  def __post_init__(self):
    if not isinstance(self.receipt, (Receipt, ReceiptRef)):
      self.receipt = ReceiptRef(self.receipt)

  def execute(self):
    from taxos.tenant.unallocated_receipt.repo.update.handler import handle

    return handle(self)
