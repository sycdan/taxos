import sys

from dev import BACKEND_ROOT
from dev.clean.command import Clean

sys.path.insert(0, BACKEND_ROOT.as_posix())
from taxos import ACCESS_TOKENS_DIR, TENANTS_DIR
from taxos.tools import json


def handle(command: Clean):
  if not ACCESS_TOKENS_DIR.exists():
    print("No access_tokens/ directory found — nothing to clean.")
    return

  removed = 0
  for token_file in sorted(ACCESS_TOKENS_DIR.glob("*.json")):
    try:
      data = json.load(token_file)
      tenant_guid = data.get("tenant")
      if tenant_guid and not (TENANTS_DIR / tenant_guid).exists():
        token_file.unlink()
        print(
          f"  removed orphaned token {token_file.stem[:12]}… (tenant {tenant_guid})"
        )
        removed += 1
    except Exception as e:
      print(f"  warning: could not read {token_file.name}: {e}")

  if removed:
    print(f"✅ Removed {removed} orphaned token(s).")
  else:
    print("✅ No orphaned tokens found.")
