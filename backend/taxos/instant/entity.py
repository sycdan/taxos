from dataclasses import dataclass, field
from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo
import tzdata


@dataclass
class Instant:
  when: datetime
  where: tzinfo = field(init=False)

  def __post_init__(self):
    if isinstance(self.when, str):
      if "@" not in self.when:
        raise ValueError("Timestamp string must include timezone info using '@'.")
      iso, tz = self.when.split("@", 1)
      self.when = datetime.fromisoformat(iso).astimezone(ZoneInfo(tz))

    if self.when.tzinfo is None:
      raise ValueError("Timestamp must be timezone-aware.")
    self.where = self.when.tzinfo

  def __str__(self) -> str:
    return f"{self.when.isoformat()}@{self.where}"


o = Instant(datetime.now().astimezone())
print(o)
print(o)
