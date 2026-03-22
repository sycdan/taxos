from dataclasses import dataclass


@dataclass
class Nuke:
  """Tear down app containers and wipe all tenant data."""

  def execute(self):
    from dev.nuke.handler import handle

    handle(self)
