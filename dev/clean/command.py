from dataclasses import dataclass


@dataclass
class Clean:
  """Remove test tenants and orphaned access tokens."""

  def execute(self):
    from dev.clean.handler import handle

    handle(self)
