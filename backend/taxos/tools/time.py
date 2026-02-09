from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def parse_datetime(value: datetime | str, zone: str = "UTC") -> datetime:
  """
  Parses a datetime string in ISO 8601 format, with optional timezone information.
  If the string does not contain timezone information, it is assumed to be in UTC.
  """
  try:
    if isinstance(value, datetime):
      dt = value
    else:
      dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
      dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(zone))
  except ValueError as e:
    raise ValueError(f"Invalid datetime format: {value}") from e
