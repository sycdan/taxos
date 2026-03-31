from dataclasses import dataclass, field
from uuid import UUID

from taxos import concepts
from taxos.tools.guid import parse_guid


@dataclass(frozen=True)
class Bucket:
  class DoesNotExist(FileNotFoundError):
    pass

  guid: UUID
  name: str

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      object.__setattr__(self, "guid", UUID(self.guid))

  def __hash__(self) -> int:
    return hash(self.guid)


@dataclass
class BucketRef:
  key: str = field(
    repr=False,
    doc="A plain-text reference to a bucket within the current tenant.",
  )
  guid: UUID = field(
    default=concepts.UNSPECIFIED,
    doc="A unique identifier for a bucket. If unspecified, it will be parsed from the key.",
  )

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)

    if self.guid == concepts.UNSPECIFIED:
      if not (key := str(self.key).strip()):
        raise ValueError("BucketRef key cannot be empty or whitespace.")
      if guid := parse_guid(key):
        self.guid = guid
      else:
        raise ValueError(f"Failed to parse BucketRef key: {self.key}")

  def __hash__(self) -> int:
    return hash(self.guid)


@dataclass(frozen=True)
class UnallocatedBucket(Bucket):
  guid: UUID = concepts.UNALLOCATED_BUCKET_SINGLETON
  name: str = "Unallocated"
