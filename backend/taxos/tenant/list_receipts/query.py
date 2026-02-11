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
  bucket: Union[Bucket, BucketRef, str] = field(
    metadata={
      "help": "Include only receipts allocated to this bucket.",
    },
  )

  def __post_init__(self):
    if not isinstance(self.bucket, (Bucket, BucketRef)):
      self.bucket = BucketRef(self.bucket)

  def execute(self):
    from taxos.tenant.list_receipts.handler import handle

    return handle(self)
