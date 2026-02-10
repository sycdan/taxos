from dataclasses import dataclass


@dataclass
class CreateBucket:
  name: str

  def __post_init__(self):
    if name := str(self.name or "").strip():
      self.name = name
    else:
      raise ValueError("Bucket name cannot be empty or whitespace.")

  def execute(self):
    from taxos.bucket.create.handler import handle

    return handle(self)
