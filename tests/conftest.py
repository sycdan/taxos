import json
from pathlib import Path
from types import FunctionType

import pytest
from scaf.cli import main as _scaf


@pytest.fixture
def scaf(capsys) -> FunctionType:
  def call_scaf(action: str, args: list[str]):
    _scaf(
      [
        Path(__file__).parent.parent.as_posix(),
        "--call",
        action,
        "--",
      ]
      + args
    )
    captured = capsys.readouterr()
    if captured.err:
      raise RuntimeError(f"scaf {action} failed: {captured.err}")
    return json.loads(captured.out)

  return call_scaf
