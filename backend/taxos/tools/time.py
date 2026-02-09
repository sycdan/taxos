from datetime import datetime
from zoneinfo import ZoneInfo


def parse_datetime(value: datetime | str, zone: str = "UTC") -> datetime:
  try:
    tz = ZoneInfo(zone.strip())
    if isinstance(value, str):
      dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
      dt = value
    if dt.tzinfo is None:
      dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz)
  except ValueError as e:
    raise ValueError(f"Invalid datetime format: {value}") from e
