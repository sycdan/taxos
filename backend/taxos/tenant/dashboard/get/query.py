from dataclasses import dataclass, field

from taxos.tenant.dashboard.entity import Dashboard


@dataclass
class GetDashboard:
  months: list[str] = field(default_factory=list)
  vendor: str | None = None

  def execute(self) -> Dashboard:
    from taxos.tenant.dashboard.get.handler import handle

    return handle(self)
