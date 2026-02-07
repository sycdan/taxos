from dataclasses import dataclass

from taxos.bucket.entity import BucketRef


@dataclass
class UpdateBucket:
  ref: BucketRef
  name: str

  def execute(self, tenant_guid=None):
    from taxos.bucket.update.handler import handle

    return handle(self, tenant_guid)
