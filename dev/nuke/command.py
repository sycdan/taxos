from dataclasses import dataclass


@dataclass
class NukeDev:
  """Reset the dev environment."""

  def execute(self):
    from dev.nuke.handler import handle

    handle(self)
