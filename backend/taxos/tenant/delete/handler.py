import shutil

from taxos.tenant.delete.command import DeleteTenant
from taxos.tenant.load.query import LoadTenant


def handle(command: DeleteTenant):
  try:
    tenant = LoadTenant(ref=command.ref).execute()
    if tenant.content_dir.exists():
      shutil.rmtree(tenant.content_dir)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
