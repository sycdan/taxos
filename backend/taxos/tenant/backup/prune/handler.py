import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from taxos import BACKUPS_DIR
from taxos.context.tools import require_tenant
from taxos.tenant.backup.prune.command import PruneBackups

logger = logging.getLogger(__name__)

_TS_RE = re.compile(r"_(\d{8}T\d{6})\.zip$")


def _parse_ts(path: Path) -> datetime | None:
  m = _TS_RE.search(path.name)
  if not m:
    return None
  try:
    return datetime.strptime(m.group(1), "%Y%m%dT%H%M%S")
  except ValueError:
    return None


def _bucket_key(
  ts: datetime,
  now: datetime,
  keep_daily: int,
  keep_weekly: int,
  keep_monthly: int,
  keep_yearly: int,
) -> tuple | None:
  age = now - ts
  daily_end = timedelta(days=keep_daily)
  weekly_end = daily_end + timedelta(weeks=keep_weekly)
  monthly_end = weekly_end + timedelta(days=keep_monthly * 30)
  yearly_end = monthly_end + timedelta(days=keep_yearly * 365)

  if age <= daily_end:
    return ("daily", ts.date())
  if age <= weekly_end:
    iso = ts.isocalendar()
    return ("weekly", iso.year, iso.week)
  if age <= monthly_end:
    return ("monthly", ts.year, ts.month)
  if keep_yearly > 0 and age <= yearly_end:
    return ("yearly", ts.year)
  return None


def handle(command: PruneBackups) -> list[Path]:
  tenant = require_tenant()
  now = datetime.now()

  files = [
    (path, ts)
    for path in BACKUPS_DIR.glob(f"{tenant.name}_*.zip")
    if (ts := _parse_ts(path)) is not None
  ]

  buckets: dict[tuple, list[tuple[datetime, Path]]] = {}
  to_delete: list[Path] = []

  for path, ts in files:
    key = _bucket_key(
      ts, now,
      command.keep_daily,
      command.keep_weekly,
      command.keep_monthly,
      command.keep_yearly,
    )
    if key is None:
      to_delete.append(path)
    else:
      buckets.setdefault(key, []).append((ts, path))

  for entries in buckets.values():
    entries.sort(key=lambda e: e[0], reverse=True)
    for _, path in entries[1:]:
      to_delete.append(path)

  for path in to_delete:
    logger.info("Pruning %s", path.name)
    path.unlink()

  logger.info(
    "Pruned %d backup(s) for tenant %s, %d remain",
    len(to_delete),
    tenant.name,
    len(files) - len(to_delete),
  )
  return to_delete
