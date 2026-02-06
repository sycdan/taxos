from dataclasses import dataclass

from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class AccessToken:
  key: str
  tenant: Tenant | TenantRef

  def __post_init__(self):
    if not self.key or not self.key.strip():
      raise ValueError("key cannot be empty.")
    if not self.tenant:
      raise ValueError("tenant must be provided.")