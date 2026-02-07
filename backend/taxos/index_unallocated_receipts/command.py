from dataclasses import dataclass
from typing import Union

from taxos.tenant.entity import Tenant, TenantRef


@dataclass
class IndexUnallocatedReceipts:
  """Index all unallocated receipts for a tenant."""

  tenant: Union[Tenant, TenantRef]

  def execute(self):
    from taxos.index_unallocated_receipts.handler import handle

    return handle(self)
