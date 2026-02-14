from dataclasses import dataclass, field

from taxos.vendor.entity import Vendor, VendorRef


@dataclass
class VendorRepo:
  index: dict[VendorRef, Vendor] = field(default_factory=dict, init=False, repr=False)

  def add(self, vendor: Vendor):
    """idempotent"""
    if not isinstance(vendor, Vendor):
      raise ValueError("VendorRepo.add requires a Vendor instance.")
    ref = VendorRef(vendor.guid.hex)
    self.index[ref] = vendor

  def get(self, ref: VendorRef) -> Vendor | None:
    if not isinstance(ref, VendorRef):
      raise ValueError("VendorRepo.get requires a VendorRef instance.")
    try:
      return self.index[ref]
    except KeyError:
      return None
