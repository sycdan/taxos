from dataclasses import dataclass, field


@dataclass
class Seed:
  """Reset the dev environment."""

  nuke: bool = field(
    default=False,
    metadata={"help": "Whether to nuke the dev environment before seeding."},
  )

  def execute(self):
    from dev.seed.handler import handle

    handle(self)
