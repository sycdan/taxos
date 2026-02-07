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
  name = folder.name
  try:
    try:
      return UUID(name)
    except ValueError:
      return UUID(name.split("_")[1])
  except (IndexError, ValueError):
    logger.warning(f"Failed to parse GUID from folder name: {name}")
    return None
