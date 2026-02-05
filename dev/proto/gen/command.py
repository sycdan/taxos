from dataclasses import dataclass


@dataclass
class GenProto:
  """Generate code from protos."""

  def execute(self):
    from dev.proto.gen.handler import handle

    return handle(self)
