import json

from taxos.bucket.entity import Bucket
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.tools import get_state_file


def handle(command: LoadBucket):
  guid = command.ref.guid
  state_file = get_state_file(guid)

  if not state_file.exists():
    raise RuntimeError(f"Bucket {guid} does not exist.")

  state = {}
  if text := state_file.read_text().strip():
    state.update(json.loads(text))

  return Bucket(guid, state.get("name", guid))
