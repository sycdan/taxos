import logging
from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = ZoneInfo("UTC")

logger = logging.getLogger(__name__)


def parse_datetime(when: datetime | str, where: ZoneInfo | str | None = None) -> datetime:
  logger.debug(f"{when=}, {where=}")
  if not where:
    where = DEFAULT_TIMEZONE

  try:
    if not isinstance(where, ZoneInfo):
      where = ZoneInfo(where.strip())
  except Exception as e:
    raise ValueError(f"Invalid timezone: {where}") from e

  try:
    if not isinstance(when, datetime):
      when = datetime.fromisoformat(when.strip().replace("Z", "+00:00"))
  except Exception as e:
    raise ValueError(f"Invalid datetime: {when}") from e

  if when.tzinfo is None:
    when = when.replace(tzinfo=where)

  when = when.astimezone(tz=where)
  logger.debug(f"Parsed datetime: {when}")
  return when
