import dataclasses
import json


class _CustomJSONEncoder(json.JSONEncoder):
  def default(self, obj):
    if dataclasses.is_dataclass(obj):
      return dataclasses.asdict(obj)  # type: ignore

    try:
      return super().default(obj)
    except TypeError:
      return str(obj)


def dumps(*args, **kwargs) -> str:
  return json.dumps(*args, **kwargs, cls=_CustomJSONEncoder)


def loads(*args, **kwargs):
  return json.loads(*args, **kwargs)
