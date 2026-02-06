from dataclasses import dataclass

from taxos.tenant.entity import TenantRef


@dataclass
class GenerateAccessToken:
  tenant_ref: TenantRef

  def execute(self):
    from taxos.access.token.generate.handler import handle

    return handle(self)
