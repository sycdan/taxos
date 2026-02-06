from dataclasses import dataclass

from taxos.tenant.entity import Tenant


@dataclass
class AuthenticateTenant:
  token: str

  def execute(self) -> Tenant:
    from taxos.access.authenticate_tenant.handler import handle

    return handle(self)
