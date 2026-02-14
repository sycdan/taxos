from pathlib import Path
from uuid import UUID

from taxos import TENANTS_DIR


def get_content_dir(guid: UUID) -> Path:
  return Path(TENANTS_DIR) / guid.hex


def get_state_file(guid: UUID) -> Path:
  content_dir = get_content_dir(guid)
  return content_dir / "state.json"


def get_buckets_dir(tenant_guid: UUID) -> Path:
  tenant_dir = get_content_dir(tenant_guid)
  return tenant_dir / "buckets"


def get_receipts_dir(tenant_guid: UUID) -> Path:
  tenant_dir = get_content_dir(tenant_guid)
  return tenant_dir / "receipts"


def get_files_dir(tenant_guid: UUID) -> Path:
  tenant_dir = get_content_dir(tenant_guid)
  return tenant_dir / "files"


def get_vendors_dir(tenant_guid: UUID) -> Path:
  tenant_dir = get_content_dir(tenant_guid)
  return tenant_dir / "vendors"
