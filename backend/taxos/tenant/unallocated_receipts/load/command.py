from dataclasses import dataclass
from typing import Union

from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class LoadUnallocatedReceipts:
  tenant: Union[Tenant, TenantRef]

  def __post_init__(self):
    if not isinstance(self.tenant, (Tenant, TenantRef)):
      raise ValueError("tenant must be a Tenant or TenantRef instance.")

  def execute(self):
    from taxos.tenant.unallocated_receipts.load.handler import handle

    return handle(self)
