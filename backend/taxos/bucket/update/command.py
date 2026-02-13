from dataclasses import dataclass
from typing import Union

from taxos.bucket.entity import BucketRef


@dataclass
class UpdateBucket:
  ref: Union[BucketRef, str]
  name: str

  def execute(self):
    from taxos.bucket.update.handler import handle

    return handle(self)
