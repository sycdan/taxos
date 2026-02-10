from dataclasses import dataclass

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class LoadReceipt:
  """Load a receipt by its GUID."""

  ref: ReceiptRef

  def __post_init__(self):
    if not isinstance(self.ref, ReceiptRef):
      self.ref = ReceiptRef(self.ref)

  def execute(self) -> Receipt:
    from taxos.receipt.load.handler import handle

    return handle(self)
