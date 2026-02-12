import hashlib
import logging
import zipfile
from pathlib import Path

from taxos.context.tools import require_receipt, require_tenant
from taxos.receipt.attach_file.command import AttachFile
from taxos.receipt.entity import Receipt
from taxos.receipt.repo.update.command import UpdateReceiptRepo
from taxos.receipt.save.command import SaveReceipt
from taxos.receipt.tools import get_state_file
from taxos.tenant.tools import get_files_dir
from taxos.tools import json

logger = logging.getLogger(__name__)


def handle(command: AttachFile) -> Receipt:
  logger.info(f"Attaching file {command.filepath} to receipt {command.receipt_ref}")
  tenant = require_tenant()
  receipt = require_receipt(command.receipt_ref)

  filepath = Path(command.filepath)
  if not filepath.exists():
    raise FileNotFoundError(f"File {filepath} does not exist")

  # 1. Calculate SHA-256 hash
  file_content = filepath.read_bytes()
  file_hash = hashlib.sha256(file_content).hexdigest()

  # 2. Create zip archive
  files_dir = get_files_dir(tenant.guid)
  files_dir.mkdir(parents=True, exist_ok=True)
  zip_path = files_dir / f"{file_hash}.zip"

  with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr(filepath.name, file_content)

  logger.info(f"Saved file {filepath.name} with hash {file_hash} to {zip_path}")

  # 3. Update receipt hash
  receipt.hash = file_hash

  return SaveReceipt(receipt).execute()
