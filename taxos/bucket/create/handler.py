import os

from taxos.bucket.create.command import CreateBucket
from taxos.bucket.entity import Bucket
from taxos.tools import guid, json


def handle(command: CreateBucket) -> Bucket:
  bucket = Bucket(guid.uuid7(), command.name)  # type: ignore

  if bucket.state_file.exists() and bucket.state_file.read_text().strip():
    raise RuntimeError(f"Bucket {bucket.name} already exists.")

  os.makedirs(bucket.content_folder, exist_ok=True)
  bucket.state_file.write_text(json.dumps(bucket, indent=2))
  return bucket
