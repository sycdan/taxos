from dataclasses import dataclass

from taxos.receipt.repo.entity import ReceiptRepo


@dataclass
class SaveReceiptRepo:
  """Saves the receipt repo to cache."""

  repo: ReceiptRepo

  def execute(self):
    from taxos.receipt.repo.save.handler import handle

    return handle(self)
