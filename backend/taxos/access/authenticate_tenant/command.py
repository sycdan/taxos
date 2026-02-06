from dataclasses import dataclass

from taxos.tenant.entity import Tenant


@dataclass
class Authenticate:
  access_token_key: str

  def execute(self) -> Tenant:
    from taxos.access.authenticate_tenant.handler import handle

    return handle(self)
