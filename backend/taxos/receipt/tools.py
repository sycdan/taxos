from pathlib import Path
from uuid import UUID

from taxos.tenant.tools import get_receipts_dir


def get_content_dir(tenant_guid: UUID, receipt_guid: UUID) -> Path:
  receipts_dir = get_receipts_dir(tenant_guid)
  return receipts_dir / receipt_guid.hex


def get_state_file(receipt_guid: UUID, tenant_guid: UUID) -> Path:
  content_dir = get_content_dir(tenant_guid, receipt_guid)
  return content_dir / "state.json"


def get_unallocated_file(tenant_guid: UUID) -> Path:
  content_dir = get_receipts_dir(tenant_guid)
  return content_dir / "unallocated.json"
