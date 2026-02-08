from dataclasses import dataclass

from taxos.receipt.entity import Receipt


@dataclass
class SaveReceipt:
  receipt: Receipt

  def execute(self):
    from taxos.receipt.save.handler import handle

    return handle(self)
