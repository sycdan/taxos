from pathlib import Path
from uuid import UUID

from taxos.tenant.tools import get_content_folder as get_tenant_folder


def get_content_folder(tenant_guid: UUID, receipt_guid: UUID) -> Path:
  tenant_folder = get_tenant_folder(tenant_guid)
  return tenant_folder / "receipts" / f"receipt_{receipt_guid.hex}"


def get_state_file(tenant_guid: UUID, receipt_guid: UUID) -> Path:
  content_folder = get_content_folder(tenant_guid, receipt_guid)
  return content_folder / "state.json"
