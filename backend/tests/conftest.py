import json
from pathlib import Path
from types import FunctionType

import pytest
from scaf.cli import main as _scaf


def pytest_addoption(parser):
  parser.addoption("--run-integration", action="store_true", default=False, help="run integration tests")


def pytest_collection_modifyitems(config, items):
  if config.getoption("--run-integration"):
    return  # do not skip integration tests
  skip_integration = pytest.mark.skip(reason="--run-integration not provided")
  for item in items:
    if "integration" in item.keywords:
      item.add_marker(skip_integration)


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
