from datetime import datetime

from taxos.instant.entity import Instant
from taxos.instant.now.query import Now


def handle(query: Now) -> Instant:
  now = datetime.now().astimezone()
  print(now.tzinfo)
  tzinfo = now.tzinfo
  return Instant(now, tzinfo)
