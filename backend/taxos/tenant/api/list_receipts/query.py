from dataclasses import dataclass, field
from typing import Union

from taxos.bucket.entity import Bucket, BucketRef


@dataclass
class ListReceipts:
  months: list[str] = field(
    metadata={
      "help": "List of specific month to load, e.g. ['2024-01', '2024-02'].",
    },
  )
  bucket: Union[Bucket, BucketRef, str, None] = field(
    default=None,
    metadata={
      "help": "If set, include receipts allocated to this bucket. If None, include only unallocated.",
    },
  )

  def __post_init__(self):
    if self.bucket and not isinstance(self.bucket, (Bucket, BucketRef)):
      self.bucket = BucketRef(self.bucket)

  def execute(self):
    from taxos.tenant.api.list_receipts.handler import handle

    return handle(self)
