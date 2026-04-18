from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BackupTenant:
  """Backup tenant data to a flat-directory or zip in data/backups.

  The backup mirrors the on-disk tenant state format:
    <dest>/
      state.json              (tenant guid + name)
      buckets/<guid>/state.json
      vendors/<guid>/state.json
      receipts/<guid>/state.json   (vendor field stores vendor GUID)

  If `zip` is True the directory is zipped and only the archive is kept.
  If `path` is given it overrides the auto-generated destination (the
  directory/zip will be written there instead of data/backups/).
  If `include_files` is False, file attachments will not be included in the backup.
  """

  zip: bool = False
  path: str = field(default="")
  include_files: bool = True

  def execute(self) -> Path:
    from taxos.tenant.backup.handler import handle

    return handle(self)
