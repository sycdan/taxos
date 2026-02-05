from pathlib import Path
from uuid import UUID

from taxos import RECEIPTS_DIR


def get_content_folder(guid: UUID) -> Path:
  return Path(RECEIPTS_DIR) / f"receipt_{guid.hex}"


def get_state_file(guid: UUID) -> Path:
  content_folder = get_content_folder(guid)
  return content_folder / "state.json"
