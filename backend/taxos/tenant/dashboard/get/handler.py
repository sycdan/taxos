from taxos.tenant.dashboard.entity import Dashboard
from taxos.tenant.dashboard.get.query import GetDashboard


def handle(query: GetDashboard) -> Dashboard:
  # TODO: Implement dashboard aggregation logic here
  # For now, return an empty Dashboard
  return Dashboard()
