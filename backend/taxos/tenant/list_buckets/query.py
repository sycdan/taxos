from dataclasses import dataclass


@dataclass
class ListBuckets:
  """Find all buckets."""

  def execute(self):
    from taxos.tenant.list_buckets.handler import handle

    return handle(self)
