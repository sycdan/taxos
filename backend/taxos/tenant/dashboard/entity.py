from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class GetDashboardRequest:
  months: List[str] = field(
    default_factory=list,
    metadata={
      "help": "List of specific months to load, e.g. ['2024-01', '2024-02'].",
    },
  )
  # Add more fields as needed for dashboard context


@dataclass
class Dashboard:
  # Define the shape of the dashboard entity here
  buckets: list = field(default_factory=list)
  unallocated: list = field(default_factory=list)
  # Add more fields as needed
