from dataclasses import dataclass


@dataclass
class Seed:
  """Reset the dev environment."""

  def execute(self):
    from dev.seed.handler import handle

    handle(self)
