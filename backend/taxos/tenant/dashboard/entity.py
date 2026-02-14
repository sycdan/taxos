from dataclasses import dataclass, field

from taxos.receipt.entity import Receipt


@dataclass
class BucketSummary:
  guid: str
  name: str
  total_amount: float
  receipt_count: int


@dataclass
class Dashboard:
  buckets: list[BucketSummary] = field(default_factory=list)
  unallocated: list[Receipt] = field(default_factory=list)
  vendor_names: list[str] = field(default_factory=list)
