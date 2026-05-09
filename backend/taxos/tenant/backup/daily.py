"""Back up every tenant found on disk. Safe to run multiple times per day."""

import logging
import os

from taxos import TENANTS_DIR
from taxos.context.entity import Context
from taxos.context.tools import set_context
from taxos.tenant.backup.command import BackupTenant
from taxos.tenant.backup.prune.command import PruneBackups
from taxos.tenant.entity import TenantRef
from taxos.tenant.tools import get_state_file
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)

_PRUNE_CONFIG = dict(
  keep_daily=int(os.environ.get("TAXOS_PRUNE_KEEP_DAILY", "7")),
  keep_weekly=int(os.environ.get("TAXOS_PRUNE_KEEP_WEEKLY", "5")),
  keep_monthly=int(os.environ.get("TAXOS_PRUNE_KEEP_MONTHLY", "13")),
  keep_yearly=int(os.environ.get("TAXOS_PRUNE_KEEP_YEARLY", "3")),
)


def run() -> None:
  if not TENANTS_DIR.exists():
    logger.warning("Tenants directory %s does not exist, skipping backup", TENANTS_DIR)
    return

  tenant_guids = [
    guid
    for d in TENANTS_DIR.iterdir()
    if d.is_dir()
    if (guid := parse_guid(d.name))
    if get_state_file(guid).exists()
  ]
  if not tenant_guids:
    logger.warning("No tenants found in %s", TENANTS_DIR)
    return

  logger.info("Backing up %d tenant(s)", len(tenant_guids))
  for guid in tenant_guids:
    try:
      tenant = TenantRef(str(guid)).hydrate()
      set_context(Context(tenant=tenant))
      path = BackupTenant(zip=True, include_files=False).execute()
      logger.info("Backed up tenant %s to %s", tenant.name, path)
      PruneBackups(**_PRUNE_CONFIG).execute()
    except Exception:
      logger.exception("Failed to back up tenant %s", guid)


if __name__ == "__main__":
  logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
  )
  run()
