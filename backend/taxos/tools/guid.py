import logging
from uuid import UUID

from uuid_extensions import uuid7str

logger = logging.getLogger(__name__)


def uuid7() -> UUID:
  return UUID(uuid7str())


def parse_guid(key: str) -> UUID | None:
  logger.debug(f"Parsing guid from {key=}")
  try:
    try:
      return UUID(key)
    except ValueError:
      return UUID(key.split("_")[1])
  except (IndexError, ValueError):
    logger.warning(f"Failed to parse GUID from {key=}")
    return None
