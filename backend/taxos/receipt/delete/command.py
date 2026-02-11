from dataclasses import dataclass

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class DeleteReceipt:
  ref: Receipt | ReceiptRef | str

  def __post_init__(self):
    if not isinstance(self.ref, (Receipt, ReceiptRef)):
      self.ref = ReceiptRef(self.ref)

  def execute(self):
    from taxos.receipt.delete.handler import handle

    return handle(self)
