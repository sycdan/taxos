from dataclasses import dataclass

from taxos.tenant.entity import TenantRef


@dataclass
class LoadTenant:
  ref: TenantRef

  def execute(self):
    from taxos.tenant.load.handler import handle

    return handle(self)
