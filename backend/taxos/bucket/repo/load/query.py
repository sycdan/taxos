from dataclasses import dataclass


@dataclass
class LoadBucketRepo:
  """Find all buckets."""

  def execute(self):
    from taxos.bucket.repo.load.handler import handle

    return handle(self)
