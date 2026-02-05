from dataclasses import dataclass, field


@dataclass
class CreateReceipt:
  vendor: str
  total: float
  date: str
  timezone: str
  allocations: list[dict] = field(default_factory=list)
  ref: str = ""
  notes: str = ""
  hash: str | None = None

  def __post_init__(self):
    if not self.vendor or not self.vendor.strip():
      raise ValueError("Vendor name cannot be empty or whitespace.")
    if self.total < 0:
      raise ValueError("Total amount cannot be negative.")
    if self.allocations is None:
      self.allocations = []

  def execute(self):
    from taxos.receipt.create.handler import handle

    return handle(self)
