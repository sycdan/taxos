from dataclasses import dataclass
from pathlib import Path


@dataclass
class IngestReceipt:
  file: Path | None = None
