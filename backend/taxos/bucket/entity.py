from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from uuid import UUID

from taxos.bucket.tools import get_content_dir


@dataclass
class Bucket:
  guid: UUID
  name: str
  tenant_guid: UUID

  @cached_property
  def content_dir(self) -> Path:
    return get_content_dir(self.tenant_guid, self.guid)

  @cached_property
  def state_file(self) -> Path:
    return self.content_dir / "state.json"

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)
    if not isinstance(self.tenant_guid, UUID):
      self.tenant_guid = UUID(self.tenant_guid)


@dataclass
class BucketRef:
  guid: UUID

  def __post_init__(self):
    if not self.guid:
      raise ValueError("guid must be provided for BucketRef.")
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)

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
    ref = BucketRef(bucket.guid)
    self.index[ref] = bucket

  def get(self, ref: BucketRef) -> Bucket | None:
    if not isinstance(ref, BucketRef):
      raise ValueError("BucketRepo.get requires a BucketRef instance.")
    try:
      return self.index[ref]
    except KeyError:
      return None
