from dataclasses import dataclass, field


@dataclass
class BuildImage:
  """Prepare an image for production."""

  no_proto: bool = field(
    default=False,
    metadata={"help": "Skip generating proto files."},
  )
  no_push: bool = field(
    default=False,
    metadata={"help": "Skip pushing to docker registry."},
  )
