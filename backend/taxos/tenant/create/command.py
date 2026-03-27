from dataclasses import dataclass, field
from uuid import UUID

from taxos.tools.guid import uuid7


@dataclass
class CreateTenant:
  name: str
  guid: UUID = field(
    default_factory=lambda: uuid7(),
    doc="Optional UUID. If not provided, a new UUID will be generated automatically.",
  )

  def __post_init__(self):
    if not self.name or not self.name.strip():
      raise ValueError("Tenant name cannot be empty or whitespace.")

  def execute(self):
    from taxos.tenant.create.handler import handle

    return handle(self)
