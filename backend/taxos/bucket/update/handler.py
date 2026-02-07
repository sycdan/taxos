from taxos.bucket.load.query import LoadBucket
from taxos.bucket.update.command import UpdateBucket
from taxos.tools import json


def handle(command: UpdateBucket, tenant_guid):
  bucket = LoadBucket(ref=command.ref).execute(tenant_guid)
  bucket.name = command.name

  bucket.state_file.write_text(json.dumps(bucket, indent=2))

  return bucket
