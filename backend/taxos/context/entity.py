from dataclasses import dataclass

from taxos.tenant.entity import Tenant


@dataclass
class Context:
  """Context for executing commands and queries, containing tenant information."""

  tenant: Tenant | None = None
