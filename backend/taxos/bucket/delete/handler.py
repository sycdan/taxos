import shutil

from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.load.query import LoadBucket


def handle(command: DeleteBucket, tenant_guid):
  try:
    bucket = LoadBucket(ref=command.ref).execute(tenant_guid)
    if bucket.content_dir.exists():
      shutil.rmtree(bucket.content_dir)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
