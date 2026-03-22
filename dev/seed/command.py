from dataclasses import dataclass


@dataclass
class Seed:
  """Seed the dev environment with a default tenant and access token."""

  def execute(self):
    from dev.seed.handler import handle

    handle(self)
