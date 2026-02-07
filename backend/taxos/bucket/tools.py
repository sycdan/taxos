from pathlib import Path
from uuid import UUID

from taxos.tenant.tools import get_content_folder as get_tenant_folder


def get_buckets_dir(tenant_guid: UUID) -> Path:
  tenant_folder = get_tenant_folder(tenant_guid)
  return tenant_folder / "buckets"


def get_content_folder(tenant_guid: UUID, bucket_guid: UUID) -> Path:
  return get_buckets_dir(tenant_guid) / f"bucket_{bucket_guid.hex}"


def get_state_file(tenant_guid: UUID, bucket_guid: UUID) -> Path:
  content_folder = get_content_folder(tenant_guid, bucket_guid)
  return content_folder / "state.json"
