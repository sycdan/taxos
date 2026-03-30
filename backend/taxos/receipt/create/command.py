from dataclasses import dataclass, field
from datetime import datetime
from typing import Union
from uuid import UUID

from taxos.allocation.entity import Allocation
from taxos.tools.guid import uuid7
from taxos.tools.time import parse_datetime
from taxos.vendor.entity import Vendor, VendorRef


@dataclass
class CreateReceipt:
  vendor: Vendor | VendorRef | str
  total: float
  date: Union[datetime, str]
  timezone: str
  allocations: set[Allocation] = field(default_factory=set)
  reference: str = ""
  notes: str = ""
  hash: str = field(
    default="",
    doc="SHA256 hash of the receipt file.",
  )
  guid: UUID = field(default_factory=lambda: uuid7())

  def __post_init__(self):
    if not isinstance(self.vendor, (Vendor, VendorRef)):
      if not self.vendor.strip():
        raise ValueError("Vendor name cannot be empty or whitespace.")

    if self.total < 0:
      raise ValueError("Total amount cannot be negative.")

    if not isinstance(self.date, datetime):
      self.date = parse_datetime(self.date, self.timezone)

    if self.allocations is None:
      self.allocations = set()
    for alloc in self.allocations:
      if not isinstance(alloc, Allocation):
        raise ValueError("Allocations must be a set of Allocation objects.")
    if not isinstance(self.allocations, set):
      self.allocations = set(self.allocations)

    self.reference = str(self.reference or "").strip()

  def execute(self):
    from taxos.receipt.create.handler import handle

    return handle(self)
