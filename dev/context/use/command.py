from dataclasses import dataclass

from taxos.tenant.entity import TenantRef


@dataclass
class UseContext:
  tenant: TenantRef

  def execute(self):
    from dev.context.use.handler import handle

    return handle(self)
