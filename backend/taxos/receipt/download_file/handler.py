import logging
import zipfile
from typing import Optional, Tuple

from taxos.context.tools import require_tenant
from taxos.receipt.download_file.command import DownloadFile, DownloadFileResult
from taxos.tenant.tools import get_files_dir

logger = logging.getLogger(__name__)


def _read_first_file_from_zip(zip_path) -> Optional[Tuple[str, bytes]]:
  if not zip_path.exists():
    return None

  with zipfile.ZipFile(zip_path, "r") as zipf:
    filenames = zipf.namelist()
    if not filenames:
      return None

    filename = filenames[0]
    file_data = zipf.read(filename)
    return filename, file_data


def handle(command: DownloadFile) -> DownloadFileResult:
  logger.debug(f"{command=}")

  if not (file_hash := command.file_hash.strip()):
    raise ValueError("A non-empty file hash is required.")

  tenant = require_tenant()
  files_dir = get_files_dir(tenant.guid)
  zip_path = files_dir / f"{file_hash}.zip"

  result = _read_first_file_from_zip(zip_path)
  if result is None:
    raise FileNotFoundError("No file exists with the requested hash.")

  filename, file_data = result
  file_size = len(file_data)

  logger.info(f"File hash {filename} with hash {file_hash} ({file_size} bytes)")
  return DownloadFileResult(filename=filename, file_data=file_data, file_size=file_size)
