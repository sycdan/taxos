from dataclasses import dataclass


@dataclass
class Gen:
  """Generate frontend constants from backend concepts.py."""

  def execute(self):
    from dev.gen.handler import handle

    handle(self)
