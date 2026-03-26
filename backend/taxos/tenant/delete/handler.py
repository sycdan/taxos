import shutil

from taxos import ACCESS_TOKENS_DIR, db
from taxos.tenant.delete.command import DeleteTenant
from taxos.tools import json


def handle(command: DeleteTenant):
  try:
    tenant = command.tenant.hydrate()

    # Remove all access tokens belonging to this tenant.
    if ACCESS_TOKENS_DIR.exists():
      for token_file in ACCESS_TOKENS_DIR.glob("*.json"):
        try:
          data = json.load(token_file)
          if data.get("tenant") == tenant.guid.hex:
            token_file.unlink()
        except Exception:
          pass

    if tenant.content_dir.exists():
      shutil.rmtree(tenant.content_dir)

    db.run(f"DROP DATABASE {tenant.db_name} IF EXISTS DESTROY DATA", database="system")
    return True
  except RuntimeError:
    pass  # probably does not exist
  return False
