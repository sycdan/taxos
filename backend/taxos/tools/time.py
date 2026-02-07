from datetime import datetime, timezone


def parse_datetime(value: str, zone: str = "UTC") -> datetime:
  """
  Parses a datetime string in ISO 8601 format, with optional timezone information.
  If the string does not contain timezone information, it is assumed to be in UTC.
  """
  try:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
      dt = dt.replace(tzinfo=timezone.utc)
    return dt
  except ValueError as e:
    raise ValueError(f"Invalid datetime format: {value}") from e
