import shutil
import subprocess

from taxos import DATA_DIR

from dev.nuke.command import Nuke


def handle(command: Nuke):
  print("💀 Killing app containers...")
  subprocess.run(["docker", "compose", "down", "-v", "backend", "--remove-orphans"])
  subprocess.run(["docker", "compose", "down", "-v", "frontend", "--remove-orphans"])

  print("💣 Nuking data...")
  shutil.rmtree(DATA_DIR, ignore_errors=True)

  print("✅ Dev environment nuked. Rebuild your dev container.")
