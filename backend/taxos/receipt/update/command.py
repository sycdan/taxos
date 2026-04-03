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
  reference: str = ""
  notes: str = ""
  file_attachments: dict[str, str] | None = field(
    default=None,
    doc="If None, existing attachments will be preserved. If empty dict, all attachments will be removed.",
  )

  def __post_init__(self):
    # TODO: tenant timezone
    if not isinstance(self.date, datetime):
      self.date = parse_datetime(self.date, self.timezone)

  def execute(self):
    from taxos.receipt.update.handler import handle

    return handle(self)
