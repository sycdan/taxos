from dataclasses import dataclass, field
from datetime import date
from uuid import UUID
from venv import logger

from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.tools.guid import parse_guid


def _get_month_key(date: date) -> str:
  return date.replace(day=1).strftime("%Y-%m")


@dataclass
class ReceiptRepo:
  records: dict[UUID, Receipt] = field(default_factory=dict, init=False)
  index_by_month: dict[str, set[UUID]] = field(default_factory=dict, init=False, repr=False)

  def add(self, receipt: Receipt):
    """idempotent add/update of a receipt to the repo"""
    self.records[receipt.guid] = receipt

    month_key = _get_month_key(receipt.date)
    self.index_by_month.setdefault(month_key, set()).add(receipt.guid)

  def get_by_ref(self, ref: UUID | Receipt | ReceiptRef | str) -> Receipt | None:
    if isinstance(ref, UUID):
      guid = ref
    elif isinstance(ref, (Receipt, ReceiptRef)):
      guid = ref.guid
    elif isinstance(ref, str):
      if not (guid := parse_guid(ref)):
        logger.debug(f"Invalid receipt guid string: {ref}")
        return None
    return self.records.get(guid)

  def iter_by_month(self, month_key: str):
    guids = self.index_by_month.get(month_key, set())
    for guid in guids:
      if receipt := self.get_by_ref(guid):
        yield receipt

  def remove(self, receipt: Receipt | ReceiptRef):
    """idempotent remove of a receipt from the repo"""
    if found := self.records.get(receipt.guid):
      month_key = _get_month_key(found.date)
      if month_key in self.index_by_month:
        self.index_by_month[month_key].remove(found.guid)
        if not self.index_by_month[month_key]:
          del self.index_by_month[month_key]
      del self.records[found.guid]
