from taxos import db
from taxos.context.tools import require_tenant
from taxos.vendor.entity import Vendor
from taxos.vendor.load.query import LoadVendor


def handle(query: LoadVendor) -> Vendor:
  tenant = require_tenant()
  guid = query.ref.guid
  records = db.query(
    "MATCH (v:Vendor {guid: $guid}) RETURN v.name AS name",
    {"guid": guid.hex},
    database=tenant.db_name,
  )
  if not records:
    raise Vendor.DoesNotExist(guid)
  return Vendor(guid, records[0]["name"])
