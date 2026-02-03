from dataclasses import dataclass


@dataclass
class Build:
  """Build the app."""

  no_backend: bool = False
  no_frontend: bool = False
