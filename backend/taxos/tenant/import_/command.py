from dataclasses import dataclass


@dataclass
class ImportTenant:
  """Restore tenant data into Neo4j from a JSON export file or directory.

  `source` can be:
  - Path to a JSON file produced by ExportTenant
  - Path to an old flat-file tenant directory (contains buckets/, vendors/, receipts/)
  """

  source: str

  def execute(self) -> dict:
    from taxos.tenant.import_.handler import handle
    return handle(self)
