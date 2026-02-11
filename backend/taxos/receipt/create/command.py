from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from typing import Union

from taxos.allocation.entity import Allocation
from taxos.tools.time import parse_datetime


@dataclass
class CreateReceipt:
  vendor: str
  total: float
  date: Union[datetime, str]
  timezone: str
  allocations: set[Allocation] = field(default_factory=set)
  vendor_ref: str = ""
  notes: str = ""
  hash: str = field(
    default="",
    metadata={"help": "SHA256 hash of the receipt file or data."},
  )

  def __post_init__(self):
    if not self.vendor or not self.vendor.strip():
      raise ValueError("Vendor name cannot be empty or whitespace.")
    if self.total < 0:
      raise ValueError("Total amount cannot be negative.")
    if self.allocations is None:
      self.allocations = set()
    if not isinstance(self.date, datetime):
      self.date = parse_datetime(self.date, self.timezone)
    self.vendor_ref = str(self.vendor_ref or "").strip()
    if not self.hash:
      hash_parts = [self.vendor, self.date.isoformat(), self.vendor_ref]
      self.hash = sha256("\n".join(hash_parts).encode()).hexdigest()

  def execute(self):
    from taxos.receipt.create.handler import handle

    return handle(self)
