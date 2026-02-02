from dataclasses import dataclass

from taxos.bucket.entity import Bucket, BucketRef


@dataclass
class LoadBucket:
  ref: BucketRef

  def execute(self) -> Bucket:
    from taxos.bucket.load.handler import handle

    return handle(self)
