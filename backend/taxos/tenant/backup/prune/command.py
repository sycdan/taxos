from dataclasses import dataclass
from pathlib import Path


@dataclass
class PruneBackups:
  """Prune old backups using tiered retention.

  Retention tiers (applied in order, oldest wins assignment):
    daily   — keep every backup within the last `keep_daily` days
    weekly  — keep one per ISO week for the next `keep_weekly` weeks
    monthly — keep one per calendar month for the next `keep_monthly` months
    yearly  — keep one per calendar year for the next `keep_yearly` years
    beyond  — delete

  Within each weekly/monthly/yearly bucket the newest backup is kept.
  """

  keep_daily: int = 7
  keep_weekly: int = 5
  keep_monthly: int = 13
  keep_yearly: int = 3

  def execute(self) -> list[Path]:
    from taxos.tenant.backup.prune.handler import handle

    return handle(self)
