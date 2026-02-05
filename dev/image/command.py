from dataclasses import dataclass


@dataclass
class BuildImage:
  """Prepare an image for production."""

  no_proto: bool = False
  no_docker: bool = False
