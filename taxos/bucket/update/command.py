from dataclasses import dataclass

from taxos.bucket.entity import BucketRef


@dataclass
class UpdateBucket:
  ref: BucketRef
  name: str
