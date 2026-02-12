import logging
from pathlib import Path

from taxos.allocation.entity import Allocation
from taxos.bucket.entity import BucketRef
from taxos.context.tools import require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.load.query import LoadReceipt
from taxos.receipt.tools import get_state_file
from taxos.tools import json
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def parse_allocations(data) -> set[Allocation]:
  allocations: set[Allocation] = set()
  if not isinstance(data, list):
    logger.warning("Invalid allocations data in receipt state data: %s", data)
    return allocations

  if not data:
    logger.debug("No allocations found in receipt state data")
    return allocations

  logger.debug("Parsing allocations data: %s", data)
  for pair in data:
    logger.debug(
      f"Processing allocation pair: {pair}, type: {type(pair)}, len: {len(pair) if isinstance(pair, dict) else 'N/A'}"
    )
    if not isinstance(pair, dict) or len(pair) != 2:
      logger.warning("Invalid allocation pair in receipt state data: %s", pair)
      continue

    bucket_ref_key = pair.get("bucket", pair.get("bucket_guid", pair.get("bucket_ref", "")))
    amount = pair.get("amount")
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
  logger.debug(f"Loaded receipt state from {state_file}: {state}")
  if not isinstance(state, dict):
    logger.warning("Invalid receipt state file: %s", state_file)
    return None

  allocations_data = state.get("allocations", [])
  logger.debug(f"Allocations data from file: {allocations_data}, type: {type(allocations_data)}")

  # Backwards compat
  if "state_file" in state and "guid" not in state:
    logger.debug("Found 'state_file' in receipt state, loading allocations from it for backwards compatibility")
    legacy_state_file = Path(state["state_file"])
    state["guid"] = legacy_state_file.parent.name

  if not (guid := parse_guid(str(state.get("guid")))):
    logger.warning("Invalid or missing GUID in receipt state file: %s", state_file)
    return None

  receipt = Receipt(
    guid,
    vendor=state["vendor"],
    total=state["total"],
    date=state["date"],
    timezone=state["timezone"],
    allocations=parse_allocations(allocations_data),
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
  try:
    if receipt := parse_receipt(state_file):
      return receipt
  except Exception as e:
    logger.exception(f"Failed loading receipt from state file {state_file}: {e}")
  raise Receipt.DoesNotExist(receipt_guid)
