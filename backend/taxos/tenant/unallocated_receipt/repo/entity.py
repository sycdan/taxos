from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from taxos.receipt.entity import Receipt, ReceiptRef
from taxos.tenant.unallocated_receipt.entity import UnallocatedReceipt


@dataclass
class UnallocatedReceiptRepo:
  unallocated_receipts: set[UnallocatedReceipt] = field(default_factory=set, init=False)
  index_by_month: dict[date, set[UnallocatedReceipt]] = field(default_factory=dict, init=False, repr=False)
  index_by_guid: dict[UUID, UnallocatedReceipt] = field(default_factory=dict, init=False, repr=False)

  def add(self, unallocated_receipt: UnallocatedReceipt):
    receipt = unallocated_receipt.receipt.hydrate()
    month = receipt.date.replace(day=1)
    self.index_by_month.setdefault(month, set()).add(unallocated_receipt)
    self.index_by_guid[unallocated_receipt.receipt.guid] = unallocated_receipt
    self.unallocated_receipts.add(unallocated_receipt)

  def remove(self, allocated_receipt: UnallocatedReceipt | Receipt | ReceiptRef):
    if isinstance(allocated_receipt, UnallocatedReceipt):
      receipt_guid = allocated_receipt.receipt.guid
    else:
      receipt_guid = allocated_receipt.guid

    extant = self.index_by_guid.get(receipt_guid)
    if not extant:
      return

    self.unallocated_receipts.remove(extant)
    self.index_by_month[extant.month].remove(extant)
    if not self.index_by_month[extant.month]:
      del self.index_by_month[extant.month]
    del self.index_by_guid[receipt_guid]
