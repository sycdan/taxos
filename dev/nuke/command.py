from dataclasses import dataclass, field


@dataclass
class NukeDev:
  """Reset the dev environment."""

  include_data: bool = field(
    default=False, kw_only=True, metadata={"help": "also delete all user data"}
  )

  def execute(self):
    from taxos.dev.nuke.handler import handle

    handle(self)
