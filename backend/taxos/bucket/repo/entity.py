from dataclasses import dataclass, field

from taxos.bucket.entity import Bucket, BucketRef


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
