from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ListUnallocatedReceipts:
  """Find all unallocated receipts for a tenant."""
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None

  def execute(self, tenant_guid=None):
    from taxos.list_unallocated_receipts.handler import handle

    return handle(self, tenant_guid)