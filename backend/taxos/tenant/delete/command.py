from dataclasses import dataclass

from taxos.tenant.entity import TenantRef


@dataclass
class DeleteTenant:
  ref: TenantRef

  def execute(self):
    from taxos.tenant.delete.handler import handle

    return handle(self)
