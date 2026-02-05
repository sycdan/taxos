from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from uuid import UUID

from taxos.receipt.tools import get_content_folder


@dataclass
class Receipt:
  guid: UUID
  vendor: str
  total: float
  date: str  # ISO8601 with offset
  timezone: str
  allocations: list[dict] = field(default_factory=list)
  ref: str = None
  notes: str = None
  hash: str = None

  @cached_property
  def content_folder(self) -> Path:
    return get_content_folder(self.guid)

  @cached_property
  def state_file(self) -> Path:
    return self.content_folder / "state.json"

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)


@dataclass
class ReceiptRef:
  guid: UUID

  def __post_init__(self):
    if not self.guid:
      raise ValueError("guid must be provided for ReceiptRef.")
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)

  def __hash__(self) -> int:
    return hash(self.guid)

  def hydrate(self) -> Receipt:
    from taxos.receipt.load.query import LoadReceipt

    return LoadReceipt(ref=self).execute()
