from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from uuid import UUID

from taxos.tenant.tools import get_content_dir, get_state_file
from taxos.tools.guid import parse_guid


@dataclass
class Tenant:
  guid: UUID
  name: str
  token_count: int = field(default=0, metadata={"help": "Number of access tokens issued to this tenant."})

  @cached_property
  def content_dir(self) -> Path:
    return get_content_dir(self.guid)

  @cached_property
  def state_file(self) -> Path:
    return get_state_file(self.guid)

  def __post_init__(self):
    if not isinstance(self.guid, UUID):
      self.guid = UUID(self.guid)

  def hydrate(self) -> "Tenant":
    return self


@dataclass
class TenantRef:
  key: str = field(metadata={"help": "A unique identifier for a tenant."})
  guid: UUID = field(init=False)

  def __post_init__(self):
    if guid := parse_guid(self.key):
      self.guid = guid
    else:
      raise ValueError("key must be a valid UUID")

  def __hash__(self) -> int:
    return hash(self.guid)

  def hydrate(self) -> Tenant:
    from taxos.tenant.load.query import LoadTenant

    return LoadTenant(ref=self).execute()
