from dataclasses import dataclass, field
from typing import Union

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class UpdateReceiptRepo:
  receipt: Union[Receipt, ReceiptRef]
  remove: bool = field(
    default=False,
    metadata={"help": "If True, remove the receipt from the repo instead of adding it."},
  )

  def __post_init__(self):
    if not isinstance(self.receipt, (Receipt, ReceiptRef)):
      self.receipt = ReceiptRef(self.receipt)

  def execute(self):
    from taxos.receipt.repo.update.handler import handle

    return handle(self)
