from pathlib import Path
from uuid import UUID

from taxos.tenant.tools import get_buckets_dir


def get_content_dir(tenant_guid: UUID, bucket_guid: UUID) -> Path:
  buckets_dir = get_buckets_dir(tenant_guid)
  return buckets_dir / bucket_guid.hex


def get_state_file(tenant_guid: UUID, bucket_guid: UUID) -> Path:
  content_dir = get_content_dir(tenant_guid, bucket_guid)
  return content_dir / "state.json"
