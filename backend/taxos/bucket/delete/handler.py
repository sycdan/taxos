import logging

from taxos import db
from taxos.bucket.delete.command import DeleteBucket
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_tenant

logger = logging.getLogger(__name__)


def handle(command: DeleteBucket):
  logger.debug(f"{command=}")
  tenant = require_tenant()
  ref = command.ref if isinstance(command.ref, BucketRef) else BucketRef(command.ref)
  # DETACH DELETE also removes ALLOCATED_TO edges from receipts
  result = db.query(
    "MATCH (b:Bucket {guid: $guid}) DETACH DELETE b RETURN count(b) AS n",
    {"guid": ref.guid.hex},
    database=tenant.db_name,
  )
  return result[0]["n"] > 0
