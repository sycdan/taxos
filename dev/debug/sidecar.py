#!/usr/bin/env python3
"""Debug sidecar entrypoint.

Copies debugpy into the shared /debugpy-vol so the backend can import it,
then finds the backend Python process and injects debugpy so it listens on
:5678.  Exits immediately after injection — run again (via the VS Code
launch task) whenever you need to re-attach after a hot-reload.
"""

import os
import shutil
import socket
import subprocess
import sys
import time

DEBUGPY_VOL = "/debugpy-vol"
INJECT_SCRIPT = f"{DEBUGPY_VOL}/inject.py"
ATTACH_SO = (
  f"{DEBUGPY_VOL}/debugpy/_vendored/pydevd/"
  "pydevd_attach_to_process/attach_linux_amd64.so"
)


# ---------------------------------------------------------------------------
# One-time setup: populate the shared volume
# ---------------------------------------------------------------------------


def setup_volume() -> None:
  import debugpy as _debugpy

  src = os.path.dirname(os.path.abspath(_debugpy.__file__))
  dst = os.path.join(DEBUGPY_VOL, "debugpy")
  if os.path.exists(dst):
    shutil.rmtree(dst)
  shutil.copytree(src, dst)
  print(f"[sidecar] Copied debugpy to {dst}")

  with open(INJECT_SCRIPT, "w") as f:
    f.write(
      "import sys\n"
      f"sys.path.insert(0, {DEBUGPY_VOL!r})\n"
      "import debugpy\n"
      "try:\n"
      "    debugpy.listen(('0.0.0.0', 5678))\n"
      "    print('[backend] debugpy listening on :5678')\n"
      "except RuntimeError:\n"
      "    print('[backend] debugpy already listening, skipping')\n"
    )
  print(f"[sidecar] Wrote inject script to {INJECT_SCRIPT}")


# ---------------------------------------------------------------------------
# Process detection
# ---------------------------------------------------------------------------


def find_backend_pid() -> int | None:
  """Return PID of the backend Python process, or None if not found yet."""
  current_pid = os.getpid()
  result = subprocess.run(
    ["ps", "-ewwo", "pid=,ppid=,comm=,args="],
    capture_output=True,
    text=True,
  )
  for line in result.stdout.splitlines():
    parts = line.strip().split(None, 3)
    if len(parts) != 4:
      continue
    pid_str, ppid_str, comm, args = parts
    pid = int(pid_str)
    ppid = int(ppid_str)
    if pid == current_pid:
      continue
    if comm not in {"python", "python3"}:
      continue
    if "sidecar.py" in args:
      continue
    # In this container, backend app is usually the python child of PID 1.
    if ppid == 1:
      return pid
    if any(
      needle in args
      for needle in (
        "graphql_server.py",
        "runserver.py",
        "connect_http_server",
      )
    ):
      return pid
  return None


# ---------------------------------------------------------------------------
# Injection
# ---------------------------------------------------------------------------


def inject_via_remote_exec(pid: int) -> bool:
  """Try Python 3.14 sys.remote_exec injection. Returns True on success."""
  try:
    sys.remote_exec(pid, INJECT_SCRIPT)  # type: ignore[attr-defined]
    print(f"[sidecar] sys.remote_exec succeeded for PID {pid}")
    return True
  except Exception as e:
    print(f"[sidecar] sys.remote_exec failed: {e} — falling back to gdb")
    return False


def wait_for_debugpy_port(timeout_s: int = 5) -> bool:
  deadline = time.time() + timeout_s
  while time.time() < deadline:
    with socket.socket() as s:
      s.settimeout(0.5)
      if s.connect_ex(("127.0.0.1", 5678)) == 0:
        return True
    time.sleep(0.2)
  return False


def inject_via_gdb(pid: int) -> None:
  """Inject debugpy into PID via gdb + DoAttach.

  Uses set sysroot /proc/<pid>/root so gdb can load the backend's shared
  libraries for symbol resolution.  The actual inject code lives in a file
  on the shared volume so the dlopen'd DoAttach can read it without any
  quoting hazards in the gdb command line.
  """
  # Short inject expression: load the script file from backend's filesystem.
  # The file is on the shared volume, so it's accessible from both sides.
  inject_expr = f"exec(open('{INJECT_SCRIPT}').read())"

  gdb_cmd = [
    "gdb",
    "--nw",
    "--nh",
    "--nx",
    f"--pid={pid}",
    "--batch",
    "--eval-command=set scheduler-locking off",
    "--eval-command=set architecture auto",
    f"--eval-command=set sysroot /proc/{pid}/root",
    f'--eval-command=call (void*)dlopen("{ATTACH_SO}", 2)',
    "--eval-command=sharedlibrary attach_linux_amd64",
    f'--eval-command=call (int)DoAttach(0, "{inject_expr}", 0)',
  ]

  print(f"[sidecar] Running gdb injection into PID {pid}...")
  subprocess.run(gdb_cmd, check=False, timeout=30)


def inject_debugpy(pid: int) -> None:
  if inject_via_remote_exec(pid) and wait_for_debugpy_port():
    print("[sidecar] Verified debugpy port open after sys.remote_exec")
    return
  print("[sidecar] debugpy port still closed after sys.remote_exec; using gdb")
  inject_via_gdb(pid)
  if wait_for_debugpy_port():
    print("[sidecar] Verified debugpy port open after gdb injection")
  else:
    print("[sidecar] debugpy port still closed after gdb injection")


# ---------------------------------------------------------------------------
# Main (single-shot)
# ---------------------------------------------------------------------------

FIND_BACKEND_TIMEOUT = 30  # seconds


def main() -> None:
  setup_volume()

  print("[sidecar] Waiting for backend process...")
  deadline = time.time() + FIND_BACKEND_TIMEOUT
  pid: int | None = None
  while time.time() < deadline:
    pid = find_backend_pid()
    if pid is not None:
      break
    time.sleep(1)

  if pid is None:
    print(f"[sidecar] Backend not found within {FIND_BACKEND_TIMEOUT}s — giving up")
    sys.exit(1)

  print(f"[sidecar] Found backend at PID {pid} — injecting debugpy on :5678")
  inject_debugpy(pid)
  print("[sidecar] Done — debugpy listening on :5678. Re-run this task to re-attach.")


if __name__ == "__main__":
  main()
