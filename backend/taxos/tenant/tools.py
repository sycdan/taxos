from pathlib import Path
from uuid import UUID

from taxos import TENANTS_DIR


def get_content_folder(guid: UUID) -> Path:
  return Path(TENANTS_DIR) / guid.hex


def get_state_file(guid: UUID) -> Path:
  content_folder = get_content_folder(guid)
  return content_folder / "state.json"
