from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.tools import get_state_file
from taxos.context.tools import require_tenant
from taxos.tools import json


def handle(command: LoadBucket):
  tenant = require_tenant()
  guid = command.ref.guid

  state_file = get_state_file(guid, tenant.guid)
  if state_file.exists():
    state = json.load(state_file)
    return Bucket(guid, state.get("name", guid))

  raise Bucket.DoesNotExist(guid)


