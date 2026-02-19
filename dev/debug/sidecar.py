#!/usr/bin/env python3
"""Debug sidecar entrypoint.

Copies debugpy into the shared /debugpy-vol so the backend can import it.
Then loops: finds the backend Python process, injects debugpy via gdb so it
listens on :5678, and waits for the process to exit before repeating
(handles hot-reload container restarts automatically).
"""

import os
import shutil
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
            "debugpy.listen(('0.0.0.0', 5678))\n"
            "print('[backend] debugpy listening on :5678')\n"
        )
    print(f"[sidecar] Wrote inject script to {INJECT_SCRIPT}")


# ---------------------------------------------------------------------------
# Process detection
# ---------------------------------------------------------------------------

def find_backend_pid() -> int | None:
    """Return PID of the backend Python process, or None if not found yet."""
    result = subprocess.run(
        ["ps", "-eo", "pid,comm,args"],
        capture_output=True, text=True,
    )
    for line in result.stdout.splitlines():
        parts = line.strip().split(None, 2)
        if (
            len(parts) == 3
            and parts[1] == "python"
            and "connect_http_server" in parts[2]
        ):
            return int(parts[0])
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
        "gdb", "--nw", "--nh", "--nx", f"--pid={pid}", "--batch",
        "--eval-command=set scheduler-locking off",
        "--eval-command=set architecture auto",
        f"--eval-command=set sysroot /proc/{pid}/root",
        f'--eval-command=call (void*)dlopen("{ATTACH_SO}", 2)',
        "--eval-command=sharedlibrary attach_linux_amd64",
        f'--eval-command=call (int)DoAttach(0, "{inject_expr}", 0)',
    ]

    print(f"[sidecar] Running gdb injection into PID {pid}...")
    subprocess.run(gdb_cmd)  # errors logged to stdout by gdb; || true semantics


def inject_debugpy(pid: int) -> None:
    if not inject_via_remote_exec(pid):
        inject_via_gdb(pid)


# ---------------------------------------------------------------------------
# Process lifecycle
# ---------------------------------------------------------------------------

def wait_for_exit(pid: int) -> None:
    while True:
        try:
            os.kill(pid, 0)  # signal 0 = check existence
            time.sleep(1)
        except OSError:
            break


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    setup_volume()

    while True:
        print("[sidecar] Waiting for backend process...")
        pid: int | None = None
        while pid is None:
            pid = find_backend_pid()
            if pid is None:
                time.sleep(1)

        print(f"[sidecar] Found backend at PID {pid} — injecting debugpy on :5678")
        inject_debugpy(pid)
        print(f"[sidecar] Waiting for PID {pid} to exit...")
        wait_for_exit(pid)
        print("[sidecar] Process exited — waiting for next backend process...")
        time.sleep(1)


if __name__ == "__main__":
    main()
