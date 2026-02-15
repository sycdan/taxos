import shutil
import subprocess

from taxos import DATA_DIR

from dev.nuke.command import NukeDev


def handle(command: NukeDev):
  print("💀 Killing app containers...")
  subprocess.run(["docker", "compose", "down", "-v", "backend", "--remove-orphans"])
  subprocess.run(["docker", "compose", "down", "-v", "frontend", "--remove-orphans"])

  print("💣 Nuking data...")
  shutil.rmtree(DATA_DIR, ignore_errors=True)
  DATA_DIR.mkdir(parents=True, exist_ok=True)

  print("✅ Dev environment nuked. You can now reload your dev container.")
