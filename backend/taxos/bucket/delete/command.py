from dataclasses import dataclass

from taxos.bucket.entity import BucketRef


@dataclass
class DeleteBucket:
  ref: BucketRef
