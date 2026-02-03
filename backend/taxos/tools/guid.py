import logging
from pathlib import Path
from uuid import UUID

from uuid_extensions import uuid7str

logger = logging.getLogger(__name__)


def uuid7() -> UUID:
  return UUID(uuid7str())


def parse_guid(folder: Path | str) -> UUID | None:
  logger.debug(f"{folder=}")
  if not isinstance(folder, Path):
    folder = Path(folder)
  try:
    return UUID(folder.name.split("_")[1])
  except (IndexError, ValueError):
    logger.warning(f"Failed to parse GUID from folder name: {folder.name}")
    return None
