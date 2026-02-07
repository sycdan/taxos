import dataclasses
import json
from pathlib import Path


class _CustomJSONEncoder(json.JSONEncoder):
  def default(self, obj):
    if dataclasses.is_dataclass(obj):
      return dataclasses.asdict(obj)  # type: ignore

    try:
      return super().default(obj)
    except TypeError:
      return str(obj)


def dumps(*args, **kwargs) -> str:
  kwargs.setdefault("indent", 2)
  return json.dumps(*args, **kwargs, cls=_CustomJSONEncoder)


def dump(*args, **kwargs) -> None:
  kwargs.setdefault("indent", 2)
  return json.dump(*args, **kwargs, cls=_CustomJSONEncoder)


def loads(*args, **kwargs):
  return json.loads(*args, **kwargs)


def load(file: Path, *args, **kwargs):
  return loads(file.read_text().strip(), *args, **kwargs)
