import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.vendor.entity import Vendor
from taxos.vendor.update.command import UpdateVendor

logger = logging.getLogger(__name__)


def handle(command: UpdateVendor) -> Vendor:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  records = db.query(
    """
    MATCH (v:Vendor {guid: $guid})
    SET v.name = $name, v.name_lower = toLower($name)
    WITH v
    OPTIONAL MATCH (v)<-[:FROM_VENDOR]-(r:Receipt)
    SET r.vendor = $name
    RETURN v.name AS name
    """,
    {"guid": command.ref.guid.hex, "name": command.name},
    database=tenant.db_name,
  )
  if not records:
    raise Vendor.DoesNotExist(command.ref.guid)
  return Vendor(command.ref.guid, records[0]["name"])
