import shutil

from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.load.query import LoadBucket


def handle(command: DeleteBucket):
  try:
    bucket = LoadBucket(ref=command.ref).execute()
    if bucket.content_folder.exists():
      shutil.rmtree(bucket.content_folder)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
