from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from taxos.tools.guid import parse_guid


@dataclass
class Receipt:
  class DoesNotExist(RuntimeError):
    pass

  guid: UUID
  vendor: str
  total: float
  date: datetime
  timezone: str
  allocations: list[dict] = field(default_factory=list)
  vendor_ref: str = ""
  notes: str = ""
  hash: str = ""

  @property
  def is_unallocated(self) -> bool:
    """
    A receipt is considered unallocated if:
    - it has no allocations
    - the sum of its allocations is less than its total
    """
    if not self.allocations:
      return True

    total_allocated = sum(allocation.get("amount", 0) for allocation in self.allocations)
    return total_allocated < self.total

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)
    if isinstance(self.date, str):
      self.date = datetime.fromisoformat(self.date)

  def hydrate(self):
    return self


@dataclass
class ReceiptRef:
  key: str = field(compare=False)
  guid: UUID = field(init=False)

  def __post_init__(self):
    if not (key := str(self.key).strip()):
      raise ValueError("receipt reference key cannot be empty")
    if guid := parse_guid(key):
      self.guid = guid
    else:
      raise ValueError("receipt reference key must contain a valid GUID")

  def __hash__(self) -> int:
    return hash(self.guid)

  def hydrate(self) -> Receipt:
    from taxos.receipt.load.query import LoadReceipt

    return LoadReceipt(ref=self).execute()
