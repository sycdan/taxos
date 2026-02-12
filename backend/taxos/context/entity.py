from dataclasses import dataclass, field
from uuid import uuid4

from taxos.access.token.entity import AccessToken
from taxos.tenant.entity import Tenant


@dataclass
class Context:
  """Context for executing commands and queries, containing tenant information."""

  tenant: Tenant | None = None
  access_token: AccessToken | None = None
  request_guid: str = field(
    default_factory=lambda: uuid4().hex,
    metadata={
      "help": "A unique identifier for the current request, used for tracing and logging.",
    },
  )

  def __post_init__(self):
    if self.tenant and not isinstance(self.tenant, Tenant):
      raise ValueError("tenant must be an instance of Tenant or None.")
    if self.access_token and not isinstance(self.access_token, AccessToken):
      raise ValueError("access_token must be an instance of AccessToken or None.")
    if not self.request_guid:
      raise ValueError("request_guid must be set")
