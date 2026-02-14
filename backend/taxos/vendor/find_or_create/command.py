from dataclasses import dataclass


@dataclass
class FindOrCreateVendor:
  name: str

  def __post_init__(self):
    if name := str(self.name or "").strip():
      self.name = name
    else:
      raise ValueError("Vendor name cannot be empty or whitespace.")

  def execute(self):
    from taxos.vendor.find_or_create.handler import handle

    return handle(self)
