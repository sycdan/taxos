import logging
from pathlib import Path

from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.load.query import LoadReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import json

logger = logging.getLogger(__name__)


def parse_allocations(data) -> set[Allocation]:
  allocations: set[Allocation] = set()
  if not isinstance(data, list):
    logger.warning("Invalid allocations data in receipt state file: %s", data)
    return allocations
  logger.debug("Parsing allocations data: %s", data)

  for pair in data:
    if not isinstance(pair, list) or len(pair) != 2:
      logger.warning("Invalid allocation pair in receipt state file: %s", pair)
      continue

    bucket_ref_key, amount = pair
    try:
      bucket_ref = BucketRef(bucket_ref_key)
    except ValueError as e:
      logger.warning("Invalid bucket reference in allocation pair: %s (%s)", bucket_ref_key, e)
      continue

    if not isinstance(amount, (int, float)):
      logger.warning("Invalid amount in allocation pair: %s", amount)
      continue
    allocations.add(Allocation(bucket_ref, amount))

  return allocations


def parse_receipt(state_file: Path) -> Receipt | None:
  if not state_file.exists():
    logger.warning("Receipt state file not found: %s", state_file)
    return None

  state = json.load(state_file)
  if not isinstance(state, dict):
    logger.warning("Invalid receipt state file: %s", state_file)
    return None

  receipt = Receipt(
    state["guid"],
    vendor=state["vendor"],
    total=state["total"],
    date=state["date"],
    timezone=state["timezone"],
    allocations=parse_allocations(state.get("allocations", [])),
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
