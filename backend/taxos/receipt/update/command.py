from dataclasses import dataclass
from datetime import datetime

from taxos.receipt.entity import ReceiptRef


@dataclass
class UpdateReceipt:
  ref: ReceiptRef
  vendor: str
  total: float
  date: datetime
  timezone: str
  allocations: list[dict]
  vendor_ref: str = ""
  notes: str = ""
  hash: str = ""

  def execute(self):
    from taxos.receipt.update.handler import handle

    return handle(self)
