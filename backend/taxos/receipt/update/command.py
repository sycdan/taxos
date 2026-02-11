from dataclasses import dataclass, field
from datetime import datetime
from typing import Union

from taxos.allocation.entity import Allocation
from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.tools.time import parse_datetime


@dataclass
class UpdateReceipt:
  ref: Union[Receipt, ReceiptRef, str]
  vendor: str
  total: float
  date: Union[datetime, str]
  timezone: str
  allocations: set[Allocation] = field(default_factory=set)
  vendor_ref: str = ""
  notes: str = ""
  hash: str = ""

  def __post_init__(self):
    if not isinstance(self.date, datetime):
      self.date = parse_datetime(self.date, self.timezone)

  def execute(self):
    from taxos.receipt.update.handler import handle

    return handle(self)
