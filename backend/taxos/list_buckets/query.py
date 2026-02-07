from dataclasses import dataclass


@dataclass
class ListBuckets:
  """Find all buckets."""

  def execute(self, tenant_guid=None):
    from taxos.list_buckets.handler import handle

    return handle(self, tenant_guid)
