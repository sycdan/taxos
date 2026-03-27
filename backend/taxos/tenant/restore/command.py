from dataclasses import dataclass
from pathlib import Path

@dataclass
class SeedTenant:
  """Restore tenant data into Neo4j from a JSON dump file or directory.

  `source` can be:
  - Path to a JSON file produced by DumpTenant
  - Path to an old flat-file tenant directory (contains buckets/, vendors/, receipts/)
  """

  source: Path

  def __post_init__(self):
    if not isinstance(self.source, Path):
      self.source = Path(self.source)

  def execute(self) -> dict:
    from taxos.tenant.restore.handler import handle

    return handle(self)
