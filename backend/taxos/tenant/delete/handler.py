import shutil

from taxos.tenant.delete.command import DeleteTenant


def handle(command: DeleteTenant):
  try:
    tenant = command.tenant.hydrate()
    if tenant.content_dir.exists():
      shutil.rmtree(tenant.content_dir)
      return True
  except RuntimeError:
    pass  # probably does not exist
  return False
