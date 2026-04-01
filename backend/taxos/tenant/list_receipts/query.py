from dataclasses import dataclass, field
from typing import Union

from taxos.bucket.entity import Bucket, BucketRef
from taxos.vendor.entity import Vendor, VendorRef


@dataclass
class ListReceipts:
  bucket: Union[Bucket, BucketRef, None] = field(
    default=None,
    doc="Include only receipts allocated to this bucket. Default: all.",
  )
  vendor: Union[Vendor, VendorRef, None] = field(
    default=None,
    doc="Include only receipts linked to this vendor. Default: all.",
  )
  months: list[str] = field(
    default_factory=list,
    doc="List of specific month to load, e.g. ['2024-01', '2024-02']. Default: all.",
  )

  def __post_init__(self):
    if self.bucket is not None and not isinstance(self.bucket, (Bucket, BucketRef)):
      self.bucket = BucketRef(self.bucket)
    if self.vendor is not None and not isinstance(self.vendor, (Vendor, VendorRef)):
      self.vendor = VendorRef(self.vendor)

  def execute(self):
    from taxos.tenant.list_receipts.handler import handle

    return handle(self)
