import dataclasses
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)


def collapse_refs(obj, is_child=False):
  if isinstance(obj, list):
    for idx, item in enumerate(obj):
      obj[idx] = collapse_refs(item, is_child)
    return obj

  if isinstance(obj, dict):
    if "guid" in obj and is_child:
      return obj["guid"]
    for key in list(obj.keys()):
      obj[key] = collapse_refs(obj[key], True)
    return obj

  logger.debug(f"Returning primitive value: {obj}")
  return obj


class DomainEncoder(json.JSONEncoder):
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
  domain_encoded = json.dumps(*args, **kwargs, cls=DomainEncoder)
  logger.debug(f"Domain encoded object: {domain_encoded}")
  serliazied = json.loads(domain_encoded)
  logger.debug(f"Serialized object: {serliazied}")
  flattened = collapse_refs(serliazied)
  logger.debug(f"Flattened object: {flattened}")
  return json.dumps(flattened, indent=2)


def dump(obj, fp, *args, **kwargs) -> None:
  kwargs.setdefault("indent", 2)
  text = dumps(obj, *args, **kwargs)
  return json.dump(text, fp, *args, **kwargs)


def safe_dump(obj, file: Path, *args, **kwargs) -> None:
  """Writes JSON to a file atomically by writing to a temp file and then renaming."""
  # TODO: make this more safe. maybe just use postgres!
  os.makedirs(file.parent, exist_ok=True)
  temp_file = file.with_suffix(f".tmp_{uuid.uuid4().hex[:8]}")
  with temp_file.open("w") as f:
    dump(obj, f, *args, **kwargs)
  temp_file.replace(file)


def loads(*args, **kwargs):
  return json.loads(*args, **kwargs)


def load(file: Path, *args, **kwargs):
  return loads(file.read_text().strip(), *args, **kwargs)
