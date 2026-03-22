from dataclasses import dataclass


@dataclass
class Clean:
  """Remove orphaned access tokens whose tenant no longer exists."""

  def execute(self):
    from dev.clean.handler import handle

    handle(self)
