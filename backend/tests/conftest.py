import pytest


def pytest_addoption(parser):
  parser.addoption("--run-integration", action="store_true", default=False, help="run integration tests")


def pytest_collection_modifyitems(config, items):
  if config.getoption("--run-integration"):
    return  # do not skip integration tests
  skip_integration = pytest.mark.skip(reason="--run-integration not provided")
  for item in items:
    if "integration" in item.keywords:
      item.add_marker(skip_integration)
