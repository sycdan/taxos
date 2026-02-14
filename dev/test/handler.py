import os

import pytest

from dev import BACKEND_ROOT, FRONTEND_ROOT
from dev.test.command import Test


def handle(command: Test, *args):
  cmd_args = ["--no-header", "--verbose", BACKEND_ROOT.as_posix()]
  cmd_args.extend(args)
  if not command.no_integration:
    cmd_args.append("--run-integration")
  if command.test_pattern:
    cmd_args.extend(["-k", command.test_pattern])
  pytest.main(cmd_args)

  if not command.no_integration:
    os.chdir(FRONTEND_ROOT)
    npm_cmd = "npm run test:integration"
    if command.test_pattern:
      npm_cmd += f" -- -t {command.test_pattern}"
    os.system(npm_cmd)
