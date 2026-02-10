from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from taxos.receipt.entity import Receipt, ReceiptRef


@dataclass
class ReceiptRepo:
  receipts: set[Receipt] = field(default_factory=set, init=False)
  index_by_month: dict[date, set[Receipt]] = field(default_factory=dict, init=False, repr=False)
  index_by_guid: dict[UUID, Receipt] = field(default_factory=dict, init=False, repr=False)

  def add(self, receipt: Receipt):
    month = receipt.date.replace(day=1)
    self.index_by_month.setdefault(month, set()).add(receipt)
    self.index_by_guid[receipt.guid] = receipt
    self.receipts.add(receipt)

  def remove(self, receipt: Receipt | ReceiptRef):
    if found := self.index_by_guid.get(receipt.guid):
      month = found.date.replace(day=1)
      self.receipts.remove(found)
      self.index_by_month[month].remove(found)
      if not self.index_by_month[month]:
        del self.index_by_month[month]
      del self.index_by_guid[found.guid]
