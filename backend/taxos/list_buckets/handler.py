import logging

from taxos import BUCKETS_DIR
from taxos.bucket.entity import BucketRef, BucketRepo
from taxos.bucket.load.query import LoadBucket
from taxos.list_buckets.query import ListBuckets
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def handle(query: ListBuckets):
  logger.info(f"Handling {query}")
  repo = BucketRepo()
  for content_folder in BUCKETS_DIR.iterdir():
    logger.debug(f"Checking folder: {content_folder}")
    if guid := parse_guid(content_folder):
      logger.info(f"Found bucket with GUID: {guid}")
      if bucket := LoadBucket(ref=BucketRef(guid=guid)).execute():
        repo.add(bucket)

  return repo
