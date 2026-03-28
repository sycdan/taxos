from dataclasses import dataclass, field
from typing import Union

from taxos.bucket.entity import Bucket, BucketRef


@dataclass
class ListReceipts:
  bucket: Union[Bucket, BucketRef] = field(
    metadata={
      "help": "Include only receipts allocated to this bucket.",
    },
  )
  months: list[str] = field(
    default_factory=list,
    metadata={
      "help": "List of specific month to load, e.g. ['2024-01', '2024-02']. Default: all.",
    },
  )

  def __post_init__(self):
    if not isinstance(self.bucket, (Bucket, BucketRef)):
      self.bucket = BucketRef(self.bucket)

  def execute(self):
    from taxos.tenant.list_receipts.handler import handle

    return handle(self)
