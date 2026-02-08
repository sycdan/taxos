from dataclasses import dataclass
from typing import Union

from taxos.receipt.entity import ReceiptRef
from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class IndexUnallocatedReceipts:
  """Index all unallocated receipts for a tenant, or just the one given."""

  tenant: Union[Tenant, TenantRef]
  receipt: Union[ReceiptRef, None] = None

  def execute(self):
    from taxos.index_unallocated_receipts.handler import handle

    return handle(self)
