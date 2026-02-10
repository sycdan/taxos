import dataclasses
import json
import uuid
from datetime import datetime
from pathlib import Path
from uuid import UUID


class _CustomJSONEncoder(json.JSONEncoder):
  def default(self, obj):
    if dataclasses.is_dataclass(obj):
      return dataclasses.asdict(obj)  # type: ignore
    if isinstance(obj, set):
      return list(obj)
    if isinstance(obj, bytes):
      return obj.decode("utf-8")
    if isinstance(obj, Path):
      return obj.as_posix()
    if isinstance(obj, UUID):
      return str(obj)
    if isinstance(obj, datetime):
      return obj.isoformat()
    return super().default(obj)


def dumps(*args, **kwargs) -> str:
  kwargs.setdefault("indent", 2)
  return json.dumps(*args, **kwargs, cls=_CustomJSONEncoder)


def dump(*args, **kwargs) -> None:
  kwargs.setdefault("indent", 2)
  return json.dump(*args, **kwargs, cls=_CustomJSONEncoder)


def safe_dump(obj, file: Path, *args, **kwargs) -> None:
  """Writes JSON to a file atomically by writing to a temp file and then renaming."""
  # TODO: make this more safe. maybe just use postgres!
  temp_file = file.with_suffix(f".tmp_{uuid.uuid4().hex[:8]}")
  with temp_file.open("w") as f:
    dump(obj, f, *args, **kwargs)
  temp_file.replace(file)


def loads(*args, **kwargs):
  return json.loads(*args, **kwargs)


def load(file: Path, *args, **kwargs):
  return loads(file.read_text().strip(), *args, **kwargs)
