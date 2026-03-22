import os
import shlex
import sys

import pytest

from dev import BACKEND_ROOT, FRONTEND_ROOT, REPO_ROOT
from dev.test.command import Test

sys.path.insert(0, BACKEND_ROOT.as_posix())
from taxos import ACCESS_TOKENS_DIR
from taxos.context.tools import get_default_context_file
from taxos.tools import json


def _find_token_for_current_tenant() -> str | None:
  """Scan access_tokens/ to find the token for the current default tenant."""
  try:
    context = json.load(get_default_context_file())
    tenant_guid = context.get("tenant")
    if not tenant_guid:
      return None
    for token_file in ACCESS_TOKENS_DIR.glob("*.json"):
      data = json.load(token_file)
      if data.get("tenant") == tenant_guid:
        return token_file.stem
  except Exception:
    pass
  return None


def handle(command: Test, *tests):
  pyt_args = ["--no-header", "--verbose", BACKEND_ROOT.as_posix()]
  if not command.no_integration:
    pyt_args.append("--run-integration")
  if tests:
    pyt_args.extend(["-k", " or ".join(tests)])
  pytest.main(pyt_args)

  if not command.no_integration:
    token = _find_token_for_current_tenant()
    npm_args = [
      "VITE_GRPC_API_URL=http://backend:50051",
      *([f"TAXOS_ACCESS_TOKEN={token}"] if token else []),
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
