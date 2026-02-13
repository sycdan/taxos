from dataclasses import dataclass, field
from uuid import UUID

from taxos.tools.guid import parse_guid


@dataclass
class Bucket:
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
class BucketRef:
  key: str = field(
    repr=False,
    metadata={"help": "A plain-text reference to a bucket within the current tenant."},
  )
  guid: UUID = field(
    init=False,
    metadata={"help": "A unique identifier for a bucket."},
  )

  def __post_init__(self):
    if not (key := str(self.key).strip()):
      raise ValueError("BucketRef key cannot be empty or whitespace.")
    if guid := parse_guid(key):
      self.guid = guid
    else:
      raise ValueError("key must contain a valid GUID.")

  def __hash__(self) -> int:
    return hash(self.guid)
