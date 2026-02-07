import logging
from pathlib import Path
from uuid import UUID

from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.load.query import LoadReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import json

logger = logging.getLogger(__name__)


def parse_receipt(state_file: Path) -> Receipt | None:
  if not state_file.exists():
    logger.warning(f"Receipt state file not found: {state_file}")
    return None

  state = json.load(state_file)
  if not isinstance(state, dict):
    logger.warning(f"Invalid receipt state file: {state_file}")
    return None

  receipt = Receipt(
    guid=UUID(state["guid"]),
    vendor=state["vendor"],
    total=state["total"],
    date=state["date"],
    timezone=state["timezone"],
    allocations=state.get("allocations", []),
    vendor_ref=state.get("vendor_ref", ""),
    notes=state.get("notes", ""),
    hash=state.get("hash", ""),
  )
  return receipt


def handle(query: LoadReceipt) -> Receipt:
  logger.debug(f"{query=}")
  tenant = require_tenant()
  receipt_guid = query.ref.guid
  state_file = get_state_file(receipt_guid, tenant.guid)
  if receipt := parse_receipt(state_file):
    return receipt
  raise Receipt.DoesNotExist(receipt_guid)
