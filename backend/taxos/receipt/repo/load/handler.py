import logging
import pickle

from taxos.bucket.entity import Bucket
from taxos.context.tools import require_bucket, require_receipt, require_tenant
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.entity import ReceiptRepo
from taxos.receipt.repo.load.command import LoadReceiptRepo
from taxos.receipt.repo.save.command import SaveReceiptRepo
from taxos.receipt.tools import get_repo_file
from taxos.tenant.entity import Tenant
from taxos.tenant.tools import get_receipts_dir
from taxos.tools.guid import parse_guid

logger = logging.getLogger(__name__)


def rebuild(tenant: Tenant) -> ReceiptRepo:
  logger.info(f"Rebuilding receipt repo for tenant {tenant.guid}")
  repo = ReceiptRepo()
  receipts_dir = get_receipts_dir(tenant.guid)

  if not receipts_dir.exists():
    logger.warning(f"Receipts directory does not exist for tenant {tenant.guid}: {receipts_dir}")
    return repo

  for receipt_dir in receipts_dir.iterdir():
    if not receipt_dir.is_dir():
      logger.debug(f"Skipping non-directory in receipts dir: {receipt_dir}")
      continue

    if not (receipt_guid := parse_guid(receipt_dir.stem)):
      logger.debug(f"Skipping non-guid directory in receipts dir: {receipt_dir}")
      continue

    try:
      receipt = require_receipt(receipt_guid)
      for allocation in receipt.allocations:
        try:
          require_bucket(allocation.bucket)
        except Bucket.DoesNotExist as e:
          allocation.amount = 0
          logger.warning(f"Failed to get bucket for allocation in receipt {receipt_guid}: {e}")
      repo.add(receipt)
    except Receipt.DoesNotExist:
      logger.warning(f"Skipping missing receipt during rebuild: {receipt_guid}")

  SaveReceiptRepo(repo).execute()
  return repo


def handle(command: LoadReceiptRepo) -> ReceiptRepo:
  logger.debug(f"{command=}")
  tenant = require_tenant()
  repo_file = get_repo_file(tenant.guid)

  if repo_file.exists() and command.force_rebuild:
    logger.info(f"Deleting receipt repo for tenant {tenant.guid} due to force_rebuild")
    repo_file.unlink()

  if not repo_file.exists():
    logger.info(f"No receipt index found for tenant {tenant.guid}")
    return rebuild(tenant)

  try:
    repo = pickle.load(repo_file.open("rb"))
    return repo
  except Exception as e:
    logger.warning(f"Failed to load receipt repo from file: {e}")
    return rebuild(tenant)
