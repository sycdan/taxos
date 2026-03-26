import logging

from taxos import db
from taxos.context.tools import require_tenant
from taxos.receipt.delete.command import DeleteReceipt
from taxos.receipt.entity import ReceiptRef

logger = logging.getLogger(__name__)


def handle(command: DeleteReceipt):
  logger.debug(f"{command=}")
  tenant = require_tenant()
  ref = (
    command.ref
    if isinstance(command.ref, ReceiptRef)
    else ReceiptRef(str(command.ref.guid))
  )
  result = db.query(
    "MATCH (r:Receipt {guid: $guid}) DETACH DELETE r RETURN count(r) AS n",
    {"guid": ref.guid.hex},
    database=tenant.db_name,
  )
  return result[0]["n"] > 0
