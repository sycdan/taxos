import logging

from taxos.bucket.entity import Bucket
from taxos.bucket.repo.entity import BucketRepo
from taxos.bucket.repo.load.query import LoadBucketRepo
from taxos.bucket.tools import get_buckets_dir
from taxos.context.tools import require_bucket, require_tenant
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def handle(query: LoadBucketRepo) -> BucketRepo:
  logger.debug(f"{query=}")
  tenant = require_tenant()
  repo = BucketRepo()

  buckets_dir = get_buckets_dir(tenant.guid)
  if not buckets_dir.exists():
    logger.info(f"No buckets directory found for tenant {tenant.guid}")
    return repo

  for content_dir in buckets_dir.iterdir():
    if not content_dir.is_dir():
      logger.debug(f"Skipping non-directory item: {content_dir}")
      continue

    logger.debug(f"Checking dir: {content_dir}")
    if guid := parse_guid(content_dir.name):
      logger.info(f"Found bucket with GUID: {guid}")
      try:
        if bucket := require_bucket(guid.hex):
          repo.add(bucket)
      except Bucket.DoesNotExist:
        logger.warning(f"Bucket with GUID {guid} does not exist, skipping.")

  return repo
