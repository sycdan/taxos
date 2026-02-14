import os
import shlex

import pytest

from dev import BACKEND_ROOT, FRONTEND_ROOT, REPO_ROOT
from dev.test.command import Test


def handle(command: Test, *tests):
  pyt_args = ["--no-header", "--verbose", BACKEND_ROOT.as_posix()]
  if not command.no_integration:
    pyt_args.append("--run-integration")
  if tests:
    pyt_args.extend(["-k", " or ".join(tests)])
  pytest.main(pyt_args)

  if not command.no_integration:
    npm_args = [
      "npm",
      "--prefix",
      FRONTEND_ROOT.relative_to(REPO_ROOT).as_posix(),
      "run",
      "test:integration",
      "--",
      "--reporter=verbose",
    ]
    if tests:
      npm_args.extend(["-t", shlex.quote("|".join(tests))])
    npm_cmd = " ".join(npm_args)
    os.system(npm_cmd)
