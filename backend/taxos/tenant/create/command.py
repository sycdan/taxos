from dataclasses import dataclass


@dataclass
class CreateTenant:
  name: str

  def __post_init__(self):
    if not self.name or not self.name.strip():
      raise ValueError("Tenant name cannot be empty or whitespace.")

  def execute(self):
    from taxos.tenant.create.handler import handle

    return handle(self)
