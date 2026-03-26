from dataclasses import dataclass


@dataclass
class SeedTenant:
  """Restore tenant data into Neo4j from a JSON dump file or directory.

  `source` can be:
  - Path to a JSON file produced by DumpTenant
  - Path to an old flat-file tenant directory (contains buckets/, vendors/, receipts/)
  """

  source: str

  def execute(self) -> dict:
    from taxos.tenant.seed.handler import handle

    return handle(self)
