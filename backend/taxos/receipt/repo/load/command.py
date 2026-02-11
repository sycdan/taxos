from dataclasses import dataclass, field

from taxos.receipt.repo.entity import ReceiptRepo


@dataclass
class LoadReceiptRepo:
  force_rebuild: bool = field(
    default=False,
    metadata={
      "help": "If True, force rebuild the receipt repo instead of loading from cache.",
    },
  )

  def execute(self) -> ReceiptRepo:
    from taxos.receipt.repo.load.handler import handle

    return handle(self)
