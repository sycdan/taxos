from dataclasses import dataclass


@dataclass
class DownloadFileResult:
  """Result of downloading a file."""

  filename: str
  file_data: bytes
  file_size: int


@dataclass
class DownloadFile:
  """Download a receipt file by its hash."""

  file_hash: str

  def __post_init__(self):
    if not isinstance(self.file_hash, str):
      raise TypeError("file_hash must be a string")

  def execute(self) -> DownloadFileResult:
    from taxos.receipt.download_file.handler import handle

    return handle(self)
