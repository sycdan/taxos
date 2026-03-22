from dataclasses import dataclass
from typing import Union

from taxos.vendor.entity import VendorRef


@dataclass
class UpdateVendor:
  ref: Union[VendorRef, str]
  name: str

  def __post_init__(self):
    if isinstance(self.ref, str):
      self.ref = VendorRef(self.ref)

    if not self.name.strip():
      raise ValueError("Vendor name cannot be empty.")

  def execute(self):
    from taxos.vendor.update.handler import handle

    return handle(self)
