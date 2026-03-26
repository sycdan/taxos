from dataclasses import dataclass, field


@dataclass
class ExportTenant:
  """Dump all tenant data to a JSON-serialisable dict (or write to a file).

  If `path` is empty the result is returned as a dict.
  If `path` is set the dict is written as pretty-printed JSON to that file.
  """

  path: str = ""

  def execute(self) -> dict:
    from taxos.tenant.export.handler import handle
    return handle(self)
