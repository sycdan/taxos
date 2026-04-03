import shutil
import sys
import time

from dev import BACKEND_ROOT
from dev.clean.command import Clean

sys.path.insert(0, BACKEND_ROOT.as_posix())
from taxos import ACCESS_TOKENS_DIR, BACKUPS_DIR, TENANTS_DIR
from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.entity import TenantRef
from taxos.tools import json

TEST_TENANT_NAMES = [
  "E2E Flow Test",
]


def _is_test_tenant_name(name: str) -> bool:
  return any(
    test_name.lower() in str(name).strip().lower() for test_name in TEST_TENANT_NAMES
  )


def _remove_test_tenants() -> int:
  if not TENANTS_DIR.exists():
    print("No tenants directory found - skipping test tenant cleanup.")
    return 0

  removed = 0
  for tenant_dir in sorted(TENANTS_DIR.iterdir()):
    state_file = tenant_dir / "state.json"
    if not state_file.exists():
      continue

    try:
      state = json.load(state_file)
      tenant_name = state.get("name", "")
      if not _is_test_tenant_name(tenant_name):
        continue

      if DeleteTenant(TenantRef(tenant_dir.name)).execute():
        print(f"  removed test tenant {tenant_dir.name} ({tenant_name})")
        removed += 1
    except Exception as e:
      print(f"  warning: could not process tenant {tenant_dir.name}: {e}")

  if removed:
    print(f"✅ Removed {removed} test tenant(s).")
  else:
    print("✅ No test tenants found.")
  return removed


def _remove_orphaned_tokens() -> int:
  if not ACCESS_TOKENS_DIR.exists():
    print("No access_tokens/ directory found - skipping orphaned token cleanup.")
    return 0

  removed = 0
  for token_file in sorted(ACCESS_TOKENS_DIR.glob("*.json")):
    try:
      data = json.load(token_file)
      tenant_guid = data.get("tenant")
      if tenant_guid and not (TENANTS_DIR / tenant_guid).exists():
        token_file.unlink()
        print(
          f"  removed orphaned token {token_file.stem[:12]}... (tenant {tenant_guid})"
        )
        removed += 1
    except Exception as e:
      print(f"  warning: could not read {token_file.name}: {e}")

  if removed:
    print(f"✅ Removed {removed} orphaned token(s).")
  else:
    print("✅ No orphaned tokens found.")
  return removed


def _remove_old_backups(max_age_seconds: int = 3600) -> int:
  if not BACKUPS_DIR.exists():
    print("No backups/ directory found - skipping old backup cleanup.")
    return 0

  removed = 0
  cutoff = time.time() - max_age_seconds
  for entry in sorted(BACKUPS_DIR.iterdir()):
    try:
      if entry.stat().st_mtime < cutoff:
        if entry.is_dir():
          shutil.rmtree(entry)
        else:
          entry.unlink()
        print(f"  removed old backup {entry.name}")
        removed += 1
    except Exception as e:
      print(f"  warning: could not remove backup {entry.name}: {e}")

  if removed:
    print(f"✅ Removed {removed} old backup(s).")
  else:
    print("✅ No old backups found.")
  return removed


def handle(command: Clean):
  _remove_test_tenants()
  _remove_orphaned_tokens()
  _remove_old_backups()
