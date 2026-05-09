from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.tenant.entity import Tenant

# Fixed reference: 2025-06-15 (Sunday). All _bucket_key tests use this as "now".
_NOW = datetime(2025, 6, 15, 12, 0, 0)


def _tenant(name: str = "acme") -> Tenant:
  t = Tenant(guid=uuid4(), name=name)
  set_context(Context(tenant=t))
  return t


def _make_zip(backups_dir: Path, tenant_name: str, ts: datetime) -> Path:
  path = backups_dir / f"{tenant_name}_{ts.strftime('%Y%m%dT%H%M%S')}.zip"
  path.touch()
  return path


class TestBucketKey:
  """Pure unit tests — no I/O, fixed reference datetime."""

  def _key(self, ts: datetime, **kwargs):
    from taxos.tenant.backup.prune.handler import _bucket_key

    defaults = dict(keep_daily=7, keep_weekly=5, keep_monthly=13, keep_yearly=3)
    return _bucket_key(ts, _NOW, **{**defaults, **kwargs})

  def test_within_daily_window(self):
    key = self._key(_NOW - timedelta(days=3))
    assert key is not None
    assert key[0] == "daily"

  def test_daily_boundary_kept_in(self):
    key = self._key(_NOW - timedelta(days=7))
    assert key is not None
    assert key[0] == "daily"

  def test_weekly_window(self):
    # 10 days ago = 2025-06-05 (Thu, week 23) — inside weekly window
    key = self._key(_NOW - timedelta(days=10))
    assert key is not None
    assert key[0] == "weekly"

  def test_monthly_window(self):
    # 100 days ago — past weekly_end (42d), within monthly_end (432d)
    key = self._key(_NOW - timedelta(days=100))
    assert key is not None
    assert key[0] == "monthly"

  def test_yearly_window(self):
    # 500 days ago — past monthly_end, within yearly_end (~1527d)
    key = self._key(_NOW - timedelta(days=500))
    assert key is not None
    assert key[0] == "yearly"

  def test_beyond_retention_returns_none(self):
    assert self._key(_NOW - timedelta(days=2000)) is None

  def test_keep_yearly_zero_returns_none_in_yearly_zone(self):
    assert self._key(_NOW - timedelta(days=500), keep_yearly=0) is None

  def test_same_week_same_bucket(self):
    # 2025-06-04 (Wed) and 2025-06-05 (Thu) are both ISO week 23
    ts_wed = datetime(2025, 6, 4, 10, 0, 0)
    ts_thu = datetime(2025, 6, 5, 10, 0, 0)
    assert self._key(ts_wed) == self._key(ts_thu)

  def test_different_weeks_different_bucket(self):
    # 2025-05-29 (Thu, week 22) vs 2025-06-05 (Thu, week 23)
    ts_week22 = datetime(2025, 5, 29, 10, 0, 0)
    ts_week23 = datetime(2025, 6, 5, 10, 0, 0)
    assert self._key(ts_week22) != self._key(ts_week23)

  def test_same_month_same_bucket(self):
    ts1 = datetime(2025, 2, 1, 10, 0, 0)
    ts2 = datetime(2025, 2, 15, 10, 0, 0)
    k1 = self._key(ts1)
    k2 = self._key(ts2)
    assert k1 is not None and k2 is not None
    assert k1 == k2

  def test_different_months_different_bucket(self):
    ts1 = datetime(2025, 2, 28, 10, 0, 0)
    ts2 = datetime(2025, 3, 1, 10, 0, 0)
    assert self._key(ts1) != self._key(ts2)


class TestPruneBackupsHandler:
  """Filesystem tests — tmp_path, patched BACKUPS_DIR and datetime.now."""

  def _run(self, tmp_path: Path, command_kwargs: dict | None = None) -> list[Path]:
    from taxos.tenant.backup.prune.command import PruneBackups

    kwargs = command_kwargs or {}
    with (
      patch("taxos.tenant.backup.prune.handler.BACKUPS_DIR", tmp_path),
      patch("taxos.tenant.backup.prune.handler.datetime") as mock_dt,
    ):
      mock_dt.now.return_value = _NOW
      mock_dt.strptime.side_effect = datetime.strptime
      return PruneBackups(**kwargs).execute()

  def test_daily_window_keeps_latest_per_day(self, tmp_path):
    t = _tenant()
    files = [
      _make_zip(tmp_path, t.name, _NOW - timedelta(hours=h))
      for h in range(0, 24 * 6, 6)
    ]

    expected_keep_by_day: dict[date, Path] = {}
    for f in files:
      ts = datetime.strptime(f.stem.split("_")[-1], "%Y%m%dT%H%M%S")
      expected_keep_by_day.setdefault(ts.date(), f)

    deleted = self._run(tmp_path)

    expected_kept = set(expected_keep_by_day.values())
    assert set(deleted) == set(files) - expected_kept
    assert all(f.exists() for f in expected_kept)

  def test_weekly_bucket_keeps_newest(self, tmp_path):
    t = _tenant()
    # Both in ISO week 23, outside daily window
    older = _make_zip(tmp_path, t.name, datetime(2025, 6, 4, 8, 0, 0))
    newer = _make_zip(tmp_path, t.name, datetime(2025, 6, 5, 8, 0, 0))

    deleted = self._run(tmp_path)

    assert older in deleted
    assert not older.exists()
    assert newer.exists()

  def test_monthly_bucket_keeps_newest(self, tmp_path):
    t = _tenant()
    # Both in March 2025, in monthly window (~90-100 days ago)
    older = _make_zip(tmp_path, t.name, datetime(2025, 3, 1, 8, 0, 0))
    newer = _make_zip(tmp_path, t.name, datetime(2025, 3, 15, 8, 0, 0))

    deleted = self._run(tmp_path)

    assert older in deleted
    assert not older.exists()
    assert newer.exists()

  def test_beyond_retention_deleted(self, tmp_path):
    t = _tenant()
    ancient = _make_zip(tmp_path, t.name, datetime(2020, 1, 1, 8, 0, 0))

    deleted = self._run(tmp_path)

    assert ancient in deleted
    assert not ancient.exists()

  def test_ignores_other_tenant_files(self, tmp_path):
    _tenant(name="acme")
    unrelated = _make_zip(tmp_path, "other", _NOW - timedelta(days=1))

    deleted = self._run(tmp_path)

    assert unrelated not in deleted
    assert unrelated.exists()

  def test_ignores_unparseable_filenames(self, tmp_path):
    t = _tenant()
    bad = tmp_path / f"{t.name}_notadate.zip"
    bad.touch()

    deleted = self._run(tmp_path)

    assert bad not in deleted
    assert bad.exists()
