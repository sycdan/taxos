from dataclasses import dataclass

from taxos.receipt.entity import ReceiptRef


@dataclass
class DeleteReceipt:
  ref: ReceiptRef

  def execute(self):
    from taxos.receipt.delete.handler import handle

    return handle(self)
