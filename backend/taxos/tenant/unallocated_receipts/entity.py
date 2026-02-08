from dataclasses import dataclass, field

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class UnallocatedReceipts:
  receipts: list[Receipt] = field(default_factory=list)
  index: dict[str, set[str]] = field(default_factory=dict)

  def add(self, receipt_ref: ReceiptRef):
    self.receipts.append(receipt_ref)
    month = receipt_ref.date.strftime("%Y-%m")
    self.index.setdefault(month, set()).add(receipt_ref.guid.hex)


#   index: dict[BucketRef, Bucket] = field(default_factory=dict, init=False, repr=False)

#   def add(self, bucket: Bucket):
#     """idempotent"""
#     if not isinstance(bucket, Bucket):
#       raise ValueError("BucketRepo.add requires a Bucket instance.")
#     ref = BucketRef(bucket.guid.hex)
#     self.index[ref] = bucket

#   def get(self, ref: BucketRef) -> Bucket | None:
#     if not isinstance(ref, BucketRef):
#       raise ValueError("BucketRepo.get requires a BucketRef instance.")
#     try:
#       return self.index[ref]
#     except KeyError:
#       return None
