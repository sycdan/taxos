import logging

from taxos.bucket.entity import Bucket, BucketRef
from taxos.bucket.tools import get_buckets_dir
from taxos.context.tools import require_tenant
from taxos.tenant.list_buckets.query import ListBuckets
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def handle(query: ListBuckets):
  logger.debug(f"{query=}")
  buckets: list[Bucket] = []
  tenant = require_tenant()
  buckets_dir = get_buckets_dir(tenant.guid)

  if not buckets_dir.exists():
    logger.info(f"No buckets directory found for tenant {tenant.guid}")
    return buckets

  for content_dir in buckets_dir.iterdir():
    if not content_dir.is_dir():
      logger.debug(f"Skipping non-directory item: {content_dir}")
      continue
    logger.debug(f"Checking dir: {content_dir}")
    if guid := parse_guid(content_dir.name):
      logger.info(f"Found bucket with GUID: {guid}")
      if bucket := BucketRef(guid.hex).hydrate():
        buckets.append(bucket)

  return buckets
