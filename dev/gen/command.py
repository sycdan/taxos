from dataclasses import dataclass


@dataclass
class Gen:
  """Generate code from protos."""

  no_backend: bool = False
  no_frontend: bool = True
