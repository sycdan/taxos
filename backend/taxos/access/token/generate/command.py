from dataclasses import dataclass
from typing import Union

from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class GenerateAccessToken:
  tenant: Union[Tenant, TenantRef]

  def execute(self):
    from taxos.access.token.generate.handler import handle

    return handle(self)
