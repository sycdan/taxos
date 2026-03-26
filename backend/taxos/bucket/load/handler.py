from taxos import db
from taxos.bucket.entity import Bucket
from taxos.bucket.load.query import LoadBucket
from taxos.context.tools import require_tenant


def handle(command: LoadBucket):
  tenant = require_tenant()
  guid = command.ref.guid
  records = db.query(
    "MATCH (b:Bucket {guid: $guid}) RETURN b.name AS name",
    {"guid": guid.hex},
    database=tenant.db_name,
  )
  if not records:
    raise Bucket.DoesNotExist(guid)
  return Bucket(guid, records[0]["name"])
