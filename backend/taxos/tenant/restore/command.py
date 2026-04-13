from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RestoreTenant:
  """Restore tenant data into Neo4j from a JSON backup file or directory.

  `source` can be:
  - Path to a JSON file produced by BackupTenant
  - Path to an old flat-file tenant directory (contains buckets/, vendors/, receipts/)

  If `include_files` is False, file attachments will not be restored from the backup.
  """

  source: Path
  name: str = "Restored Tenant"
  include_files: bool = True
  nuke: bool = field(
    default=False,
    doc="If True, any existing tenant with the same GUID will be deleted before creating the new tenant.",
  )

  def __post_init__(self):
    if not isinstance(self.source, Path):
      self.source = Path(self.source)

  def execute(self):
    from taxos.tenant.restore.handler import handle

    return handle(self)
