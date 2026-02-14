from dataclasses import dataclass
from typing import Union

from taxos.bucket.entity import Bucket, BucketRef


@dataclass
class DeleteBucket:
  ref: Union[Bucket, BucketRef, str]

  def __post_init__(self):
    if not isinstance(self.ref, (Bucket, BucketRef)):
      self.ref = BucketRef(self.ref)

  def execute(self):
    from taxos.bucket.delete.handler import handle

    return handle(self)
