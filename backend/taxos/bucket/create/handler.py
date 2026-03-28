import logging

from taxos import db
from taxos.bucket.create.command import CreateBucket
from taxos.bucket.entity import Bucket
from taxos.context.tools import require_tenant

logger = logging.getLogger(__name__)


def handle(command: CreateBucket) -> Bucket:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  bucket = Bucket(command.guid, command.name)
  db.run(
    "CREATE (:Bucket {guid: $guid, name: $name})",
    {"guid": bucket.guid.hex, "name": bucket.name},
    database=tenant.db_name,
  )
  return bucket
