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
  allocations: list[tuple[str, float]] = field(
    default_factory=list, metadata={"help": "List of (bucket_ref, amount) pairs."}
  )
  vendor_ref: str = ""
  notes: str = ""
  hash: str = ""

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)
    if isinstance(self.date, str):
      self.date = datetime.fromisoformat(self.date)

  def __hash__(self) -> int:
    return hash(self.guid)

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

  def __str__(self) -> str:
    return f"receipt_{self.guid.hex}"

  def hydrate(self) -> Receipt:
    from taxos.receipt.load.query import LoadReceipt

    return LoadReceipt(ref=self).execute()
