from dataclasses import dataclass
from typing import Union

from taxos.bucket.entity import Bucket, BucketRef


@dataclass
class Allocation:
  bucket: Union[Bucket, BucketRef]
  amount: float

  def __post_init__(self):
    if not isinstance(self.bucket, (Bucket, BucketRef)):
      self.bucket = BucketRef(self.bucket)
    if not isinstance(self.amount, (int, float)):
      self.amount = float(self.amount)

  def __hash__(self) -> int:
    return hash(self.bucket)
