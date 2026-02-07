import shutil

from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.load.query import LoadBucket


def handle(command: DeleteBucket):
  try:
    bucket = LoadBucket(ref=command.ref).execute()
    if bucket.content_dir.exists():
      shutil.rmtree(bucket.content_dir)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
