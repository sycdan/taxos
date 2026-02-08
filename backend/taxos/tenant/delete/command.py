from dataclasses import dataclass
from typing import Union

from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class DeleteTenant:
  tenant: Union[Tenant, TenantRef]

  def execute(self):
    from taxos.tenant.delete.handler import handle

    return handle(self)
