from dataclasses import dataclass
from pathlib import Path
from typing import Union

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class AttachFile:
  receipt_ref: Union[Receipt, ReceiptRef, str]
  filepath: Path

  def execute(self):
    from taxos.receipt.attach_file.handler import handle

    return handle(self)
