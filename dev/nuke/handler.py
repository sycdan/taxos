import shutil
import subprocess
import sys

sys.path.append("./backend")

from taxos import DATA_DIR

from dev.nuke.command import Nuke


def handle(command: Nuke):
  print("💀 Killing app containers...")
  subprocess.run(["docker", "compose", "down", "-v", "backend"], check=True)
  subprocess.run(["docker", "compose", "down", "-v", "frontend"], check=True)

  print("💣 Nuking data...")
  shutil.rmtree(DATA_DIR, ignore_errors=True)

  print("✅ Dev environment nuked")
  print("💡 Run dev.seed to set up again.")
