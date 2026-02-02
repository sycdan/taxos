from taxos.bucket.load.query import LoadBucket
from taxos.bucket.update.command import UpdateBucket
from taxos.tools import json


def handle(command: UpdateBucket):
  bucket = LoadBucket(ref=command.ref).execute()
  bucket.name = command.name

  bucket.state_file.write_text(json.dumps(bucket, indent=2))

  return bucket
