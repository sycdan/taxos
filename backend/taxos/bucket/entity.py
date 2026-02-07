from dataclasses import dataclass, field
from uuid import UUID

from taxos.tools.guid import parse_guid


@dataclass
class Bucket:
  class DoesNotExist(RuntimeError):
    pass

  guid: UUID
  name: str

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)


@dataclass
class BucketRef:
  key: str = field(
    metadata={"help": "A plain-text reference to a bucket within the current tenant."},
  )
  guid: UUID = field(
    init=False,
    metadata={"help": "A unique identifier for a bucket."},
  )

  def __post_init__(self):
    if not (key := self.key.strip()):
      raise ValueError("BucketRef key cannot be empty or whitespace.")
    if guid := parse_guid(key):
      self.guid = guid
    else:
      raise ValueError("key must contain a valid GUID.")

  def __hash__(self) -> int:
    return hash(self.guid)

  def hydrate(self) -> Bucket:
    from taxos.bucket.load.query import LoadBucket

    return LoadBucket(ref=self).execute()


@dataclass
class BucketRepo:
  index: dict[BucketRef, Bucket] = field(default_factory=dict, init=False, repr=False)

  def add(self, bucket: Bucket):
    """idempotent"""
    if not isinstance(bucket, Bucket):
      raise ValueError("BucketRepo.add requires a Bucket instance.")
    ref = BucketRef(bucket.guid.hex)
    self.index[ref] = bucket

  def get(self, ref: BucketRef) -> Bucket | None:
    if not isinstance(ref, BucketRef):
      raise ValueError("BucketRepo.get requires a BucketRef instance.")
    try:
      return self.index[ref]
    except KeyError:
      return None
