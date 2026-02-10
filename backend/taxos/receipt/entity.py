from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from taxos.allocation.entity import Allocation
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
  allocations: set[Allocation] = field(
    default_factory=set,
    metadata={"help": "How much of the total is assigned to which buckets."},
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


def require_receipt(ref: Receipt | ReceiptRef) -> Receipt:
  """Hydrates a ReceiptRef to a Receipt, or returns the Receipt if already hydrated.
  Raises Receipt.DoesNotExist."""
  from taxos.receipt.load.query import LoadReceipt

  if isinstance(ref, Receipt):
    return ref
  return LoadReceipt(ref).execute()
