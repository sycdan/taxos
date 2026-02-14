from pathlib import Path
from uuid import UUID

from taxos.tenant.tools import get_vendors_dir as get_tenant_vendors_dir


def get_vendors_dir(tenant_guid: UUID) -> Path:
  """Alias for consistency with other entity tools."""
  return get_tenant_vendors_dir(tenant_guid)


def get_content_dir(vendor_guid: UUID, tenant_guid: UUID) -> Path:
  vendors_dir = get_vendors_dir(tenant_guid)
  return vendors_dir / vendor_guid.hex


def get_state_file(vendor_guid: UUID, tenant_guid: UUID) -> Path:
  content_dir = get_content_dir(vendor_guid, tenant_guid)
  return content_dir / "state.json"
