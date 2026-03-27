from dataclasses import dataclass, field
from uuid import UUID

from taxos.tools import guid


@dataclass
class CreateBucket:
  name: str
  guid: UUID = field(
    default_factory=lambda: guid.uuid7(),
    doc="Optional UUID. If not provided, a new UUID will be generated automatically.",
  )

  def __post_init__(self):
    if name := str(self.name or "").strip():
      self.name = name
    else:
      raise ValueError("Bucket name cannot be empty or whitespace.")

  def execute(self):
    from taxos.bucket.create.handler import handle

    return handle(self)
