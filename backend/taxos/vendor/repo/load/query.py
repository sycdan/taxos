from dataclasses import dataclass


@dataclass
class LoadVendorRepo:
  def execute(self):
    from taxos.vendor.repo.load.handler import handle

    return handle(self)
