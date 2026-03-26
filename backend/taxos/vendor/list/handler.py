import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.vendor.entity import Vendor
from taxos.vendor.list.query import ListVendors

logger = logging.getLogger(__name__)


def handle(query: ListVendors) -> list[Vendor]:
  logger.debug(f"{query=}")
  tenant = require_tenant()
  records = db.query(
    "MATCH (v:Vendor) RETURN v.guid AS guid, v.name AS name ORDER BY toLower(v.name)",
    database=tenant.db_name,
  )
  return [Vendor(r["guid"], r["name"]) for r in records]
