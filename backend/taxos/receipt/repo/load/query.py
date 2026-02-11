from dataclasses import dataclass, field
from typing import Union

from taxos.bucket.entity import Bucket, BucketRef
from taxos.receipt.repo.entity import ReceiptRepo


@dataclass
class LoadReceiptRepo:
  months: list[str] = field(
    default_factory=list,
    metadata={
      "help": "List of month keys to load, e.g. ['2024-01', '2024-02']",
    },
  )
  bucket: Union[Bucket, BucketRef, str, None] = field(
    default=None,
    metadata={
      "help": "If set, load receipts allocated to this bucket. If None, load all.",
    },
  )
  unallocated_only: bool = field(
    default=False,
    metadata={
      "help": "If True, only load receipts without any allocations. Ignored if bucket is set.",
    },
  )

  def __post_init__(self):
    if self.bucket and not isinstance(self.bucket, (Bucket, BucketRef)):
      self.bucket = BucketRef(self.bucket)

  def execute(self) -> ReceiptRepo:
    from taxos.receipt.repo.load.handler import handle

    return handle(self)
