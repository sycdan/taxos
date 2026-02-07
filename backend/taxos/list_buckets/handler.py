import logging

from taxos.bucket.entity import BucketRef, BucketRepo
from taxos.bucket.load.query import LoadBucket
from taxos.bucket.tools import get_buckets_dir
from taxos.list_buckets.query import ListBuckets
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def handle(query: ListBuckets, tenant_guid):
  logger.info(f"Handling {query}")
  repo = BucketRepo()
  buckets_dir = get_buckets_dir(tenant_guid)

  if not buckets_dir.exists():
    logger.info(f"No buckets directory found for tenant {tenant_guid}")
    return repo

  for content_dir in buckets_dir.iterdir():
    if not content_dir.is_dir():
      logger.debug(f"Skipping non-directory item: {content_dir}")
      continue
    logger.debug(f"Checking dir: {content_dir}")
    if guid := parse_guid(content_dir):
      logger.info(f"Found bucket with GUID: {guid}")
      if bucket := LoadBucket(ref=BucketRef(guid=guid)).execute(tenant_guid):
        repo.add(bucket)

  return repo
