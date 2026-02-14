from dataclasses import dataclass

from taxos.vendor.entity import Vendor


@dataclass
class ListVendors:
  def execute(self) -> list[Vendor]:
    from taxos.vendor.list.handler import handle

    return handle(self)
