import os
import sys
import subprocess
from pathlib import Path
import pytest

from dev import BACKEND_ROOT, REPO_ROOT
from dev.test.command import Test

sys.path.insert(0, BACKEND_ROOT.as_posix())

TEST_DIR = REPO_ROOT / "test"
FRONTEND_ROOT = REPO_ROOT / "frontend"
PLAYWRIGHT_BIN = FRONTEND_ROOT / "node_modules" / ".bin" / "playwright"

def _ensure_test_node_modules():
  """Ensure test/node_modules is a symlink to frontend/node_modules.

  This gives the test/ TypeScript files access to @playwright/test and
  @types/node without a separate npm install.
  """
  link = TEST_DIR / "node_modules"
  target = Path("../frontend/node_modules")
  if not link.exists() and not link.is_symlink():
    link.symlink_to(target)


def _ensure_playwright_browsers():
  """Install Playwright browser binaries if they are not already present."""
  cache = Path.home() / ".cache" / "ms-playwright"
  # Check for any chromium_headless_shell directory — the version suffix varies.
  already_installed = (
    any(cache.glob("chromium_headless_shell-*")) if cache.exists() else False
  )
  if not already_installed:
    print("🎭 Installing Playwright browser binaries...")
    subprocess.run(
      [str(PLAYWRIGHT_BIN), "install", "--with-deps", "chromium"],
      check=True,
    )


def handle(command: Test, *tests):
  os.chdir(REPO_ROOT)

  if command.flows:
    _ensure_test_node_modules()
    _ensure_playwright_browsers()
    pw_args = [
      str(PLAYWRIGHT_BIN),
      "test",
      "--config",
      str(TEST_DIR / "playwright.config.ts"),
    ]
    if command.ui:
      pw_args.append("--ui")
    if tests:
      # --grep accepts a JS regex; join multiple names with |
      pw_args.extend(["--grep", "|".join(tests)])
    try:
      subprocess.run(pw_args, check=True)
    except subprocess.CalledProcessError as e:
      raise RuntimeError("Flow tests failed") from e
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

