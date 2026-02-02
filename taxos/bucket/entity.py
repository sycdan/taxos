from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from uuid import UUID

from taxos.bucket.tools import get_content_folder


@dataclass
class Bucket:
  guid: UUID
  name: str

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
class BucketRef:
  guid: UUID

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)

  def hydrate(self) -> Bucket:
    from taxos.bucket.load.query import LoadBucket

    if not self.guid:
      raise ValueError("Cannot hydrate BucketRef without a guid.")

    return LoadBucket(ref=self).execute()
