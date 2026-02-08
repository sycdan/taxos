from dataclasses import dataclass
from typing import Union

from taxos.receipt.entity import ReceiptRef
from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class IndexUnallocatedReceipts:
  """Index all unallocated receipts for a tenant, or just the one given."""

  tenant: Union[Tenant, TenantRef]
  receipt: Union[ReceiptRef, None] = None

  def __post_init__(self):
    if not isinstance(self.tenant, (Tenant, TenantRef)):
      raise ValueError("tenant must be a Tenant or TenantRef instance.")
    if self.receipt and not isinstance(self.receipt, ReceiptRef):
      self.receipt = ReceiptRef(self.receipt)

  def execute(self):
    from taxos.index_unallocated_receipts.handler import handle

    return handle(self)
