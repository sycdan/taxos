from dataclasses import dataclass


@dataclass
class Build:
  """Prepare an image."""

  no_proto: bool = False
  no_docker: bool = False
