import logging

from taxos import db
from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.update.command import UpdateBucket
from taxos.context.tools import require_tenant

logger = logging.getLogger(__name__)


def handle(command: UpdateBucket) -> Bucket:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  ref = command.ref if isinstance(command.ref, BucketRef) else BucketRef(command.ref)
  records = db.query(
    "MATCH (b:Bucket {guid: $guid}) SET b.name = $name RETURN b.name AS name",
    {"guid": ref.guid.hex, "name": command.name},
    database=tenant.db_name,
  )
  if not records:
    raise Bucket.DoesNotExist(ref.guid)
  return Bucket(ref.guid, records[0]["name"])
