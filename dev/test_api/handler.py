import os

import pytest

from dev import BACKEND_ROOT
from dev.test_api.command import TestApi


def handle(command: TestApi, *args):
  cmd_args = ["--no-header", "--verbose", BACKEND_ROOT.as_posix()]
  cmd_args.extend(args)
  if not command.no_integration:
    cmd_args.append("--run-integration")
  return pytest.main(cmd_args)
