from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ListUnallocatedReceipts:
  """Find all unallocated receipts for a tenant."""

  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None

  def execute(self):
    from taxos.tenant.unallocated_receipts.list.handler import handle

    return handle(self)
