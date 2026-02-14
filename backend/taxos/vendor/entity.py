from dataclasses import dataclass, field
from uuid import UUID

from taxos.tools.guid import parse_guid


@dataclass
class Vendor:
  class DoesNotExist(FileNotFoundError):
    pass

  guid: UUID
  name: str

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)

  def __hash__(self) -> int:
    return hash(self.guid)


@dataclass
class VendorRef:
  key: str = field(
    repr=False,
    metadata={"help": "A plain-text reference to a vendor within the current tenant."},
  )
  guid: UUID = field(
    init=False,
    metadata={"help": "A unique identifier for a vendor."},
  )

  def __post_init__(self):
    if not (key := str(self.key).strip()):
      raise ValueError("VendorRef key cannot be empty or whitespace.")
    if guid := parse_guid(key):
      self.guid = guid
    else:
      raise ValueError("key must contain a valid GUID.")

  def __hash__(self) -> int:
    return hash(self.guid)
