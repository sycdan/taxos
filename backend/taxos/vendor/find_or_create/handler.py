import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.tools import guid as guid_tools
from taxos.vendor.entity import Vendor
from taxos.vendor.find_or_create.command import FindOrCreateVendor

logger = logging.getLogger(__name__)


def handle(command: FindOrCreateVendor) -> Vendor:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  records = db.query(
    """
    MERGE (v:Vendor {name_lower: toLower($name)})
    ON CREATE SET v.guid = $new_guid, v.name = $name
    RETURN v.guid AS guid, v.name AS name
    """,
    {"name": command.name, "new_guid": guid_tools.uuid7().hex},
    database=tenant.db_name,
  )
  row = records[0]
  return Vendor(row["guid"], row["name"])
