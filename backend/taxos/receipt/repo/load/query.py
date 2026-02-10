from dataclasses import dataclass, field
from datetime import datetime
from typing import Union
from zoneinfo import ZoneInfo

from taxos.bucket.entity import BucketRef
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.tools.time import parse_datetime


@dataclass
class LoadReceiptRepo:
  start_date: Union[datetime, str, None] = None
  end_date: Union[datetime, str, None] = None
  timezone: Union[ZoneInfo, str, None] = None
  bucket: Union[BucketRef, str, None] = field(
    default=None,
    metadata={
      "help": "If set, load receipts allocated to this bucket. If None, load unallocated.",
    },
  )

  def __post_init__(self):
    if self.end_date and not self.start_date:
      raise ValueError("start_date is required when end_date is set")
    if (self.start_date or self.end_date) and not self.timezone:
      raise ValueError("timezone is required when start_date or end_date is set")
    if self.timezone and not isinstance(self.timezone, ZoneInfo):
      self.timezone = ZoneInfo(self.timezone)
    if self.start_date and not self.end_date:
      self.end_date = datetime.now().astimezone()
    if self.start_date and not isinstance(self.start_date, datetime):
      self.start_date = parse_datetime(self.start_date, self.timezone)
    if self.end_date and not isinstance(self.end_date, datetime):
      self.end_date = parse_datetime(self.end_date, self.timezone)
    if self.bucket and not isinstance(self.bucket, BucketRef):
      self.bucket = BucketRef(self.bucket)

  def execute(self) -> ReceiptRepo:
    from taxos.receipt.repo.load.handler import handle

    return handle(self)
