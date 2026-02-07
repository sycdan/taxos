from dataclasses import dataclass

from taxos.bucket.entity import BucketRef


@dataclass
class DeleteBucket:
  ref: BucketRef

  def execute(self):
    from taxos.bucket.delete.handler import handle

    return handle(self)
