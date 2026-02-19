import sys
from dataclasses import dataclass

sys.path.append("./backend")

from taxos.tenant.entity import TenantRef


@dataclass
class UseContext:
  tenant: TenantRef

  def execute(self):
    from dev.context.use.handler import handle

    return handle(self)
