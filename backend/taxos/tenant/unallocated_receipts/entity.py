from dataclasses import dataclass, field

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class UnallocatedReceipts:
  receipts: list[Receipt] = field(default_factory=list)
  index: dict[str, set[str]] = field(default_factory=dict)

  def add(self, receipt_ref: ReceiptRef):
    self.receipts.append(receipt_ref)
    month = receipt_ref.date.strftime("%Y-%m")
    self.index.setdefault(month, set()).add(receipt_ref.guid.hex)
