from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LoadUnallocatedReceiptRepo:
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None

  def __post_init__(self):
    if self.start_date and not isinstance(self.start_date, datetime):
      self.start_date = datetime.fromisoformat(self.start_date)
    if self.end_date and not isinstance(self.end_date, datetime):
      self.end_date = datetime.fromisoformat(self.end_date)

  def execute(self):
    from taxos.tenant.unallocated_receipt.repo.load.handler import handle

    return handle(self)
