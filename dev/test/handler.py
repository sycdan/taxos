import os
import shlex
import sys
import subprocess
from pathlib import Path
import pytest

from dev import BACKEND_ROOT, FRONTEND_ROOT, REPO_ROOT
from dev.test.command import Test

sys.path.insert(0, BACKEND_ROOT.as_posix())
from taxos import ACCESS_TOKENS_DIR
from taxos.context.tools import get_default_context_file
from taxos.tools import json

TEST_DIR = REPO_ROOT / "test"
PLAYWRIGHT_BIN = FRONTEND_ROOT / "node_modules" / ".bin" / "playwright"


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


def _ensure_test_node_modules():
  """Ensure test/node_modules is a symlink to frontend/node_modules.

  This gives the test/ TypeScript files access to @playwright/test and
  @types/node without a separate npm install.
  """
  link = TEST_DIR / "node_modules"
  target = Path("../frontend/node_modules")
  if not link.exists() and not link.is_symlink():
    link.symlink_to(target)


def handle(command: Test, *tests):
  os.chdir(REPO_ROOT)

  if command.flows:
    _ensure_test_node_modules()
    # The React app (served by the frontend container) calls the backend at
    # http://localhost:50051 (baked in by Vite from VITE_GRPC_API_URL).
    # From within the devcontainer, localhost:50051 isn't mapped to the backend
    # container, so we stand up a socat proxy for the duration of the test run.
    socat = subprocess.Popen(
      ["socat", "TCP-LISTEN:50051,fork,reuseaddr", "TCP:backend:50051"],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )
    try:
      pw_args = [
        str(PLAYWRIGHT_BIN),
        "test",
        "--config",
        str(TEST_DIR / "playwright.config.ts"),
      ]
      if tests:
        # --grep accepts a JS regex; join multiple names with |
        pw_args.extend(["--grep", "|".join(tests)])
      subprocess.run(pw_args, check=True)
    finally:
      socat.terminate()
      socat.wait()
    return

  if not command.no_backend:
    pyt_args = ["--no-header", "-s", "--verbose", BACKEND_ROOT.as_posix()]
    if not command.no_integration:
      pyt_args.append("--run-integration")
    if tests:
      pyt_args.extend(["-k", " or ".join(tests)])
    try:
      pytest.main(pyt_args)
    except SystemExit as e:
      if e.code != 0:
        raise RuntimeError("Backend tests failed") from e

  if not command.no_integration and not command.no_frontend:
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
    subprocess.run(npm_cmd, shell=True, check=True)
