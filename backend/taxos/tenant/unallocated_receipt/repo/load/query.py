from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from taxos.tenant.unallocated_receipt.repo.entity import UnallocatedReceiptRepo


@dataclass
class LoadUnallocatedReceiptRepo:
  start_date: Optional[datetime] = None
  end_date: Optional[datetime] = None
  bucket_guid: Optional[UUID] = None  # If set, load receipts allocated to this bucket. If None, load unallocated.

  def __post_init__(self):
    if self.start_date and not isinstance(self.start_date, datetime):
      self.start_date = datetime.fromisoformat(self.start_date)
    if self.end_date and not isinstance(self.end_date, datetime):
      self.end_date = datetime.fromisoformat(self.end_date)
    if self.bucket_guid and not isinstance(self.bucket_guid, UUID):
      self.bucket_guid = UUID(self.bucket_guid)

  def execute(self) -> UnallocatedReceiptRepo:
    from taxos.tenant.unallocated_receipt.repo.load.handler import handle

    return handle(self)
