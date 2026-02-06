from dataclasses import dataclass

from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class GenerateAccessToken:
  tenant: Tenant | TenantRef

  def execute(self):
    from taxos.access.token.generate.handler import handle

    return handle(self)
