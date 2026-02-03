from dataclasses import dataclass


@dataclass
class Build:
  """Prepare an image."""

  no_backend: bool = False
  no_frontend: bool = False
  no_docker: bool = False
