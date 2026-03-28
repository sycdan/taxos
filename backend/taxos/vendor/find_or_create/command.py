from dataclasses import dataclass, field
from uuid import UUID

from taxos.tools.guid import uuid7


@dataclass
class FindOrCreateVendor:
  name: str
  guid: UUID = field(default_factory=lambda: uuid7())

  def __post_init__(self):
    if name := str(self.name or "").strip():
      self.name = name
    else:
      raise ValueError("Vendor name cannot be empty or whitespace.")

  def execute(self):
    from taxos.vendor.find_or_create.handler import handle

    return handle(self)
