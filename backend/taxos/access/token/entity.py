from dataclasses import dataclass

from taxos.tenant.entity import TenantRef


@dataclass
class AccessToken:
  key: str
  tenant_ref: TenantRef

  def __post_init__(self):
    if not self.key or not self.key.strip():
      raise ValueError("key cannot be empty.")
    if not self.tenant_ref:
      raise ValueError("tenant_ref must be provided.")
