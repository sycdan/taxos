from dataclasses import dataclass

from taxos.vendor.entity import Vendor, VendorRef


@dataclass
class LoadVendor:
  ref: VendorRef | str

  def __post_init__(self):
    if not isinstance(self.ref, VendorRef):
      self.ref = VendorRef(self.ref)

  def execute(self) -> Vendor:
    from taxos.vendor.load.handler import handle

    return handle(self)
