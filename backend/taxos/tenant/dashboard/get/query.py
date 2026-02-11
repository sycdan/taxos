from dataclasses import dataclass, field
from typing import List

from taxos.tenant.dashboard.entity import Dashboard


@dataclass
class GetDashboard:
  months: List[str] = field(default_factory=list)

  def execute(self) -> Dashboard:
    from taxos.tenant.dashboard.get.handler import handle

    return handle(self)
