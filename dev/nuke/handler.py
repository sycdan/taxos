import subprocess
import shutil

from dev.nuke.command import NukeDev
from taxos import BUCKETS_DIR, RECEIPTS_DIR


def handle(command: NukeDev):
  print("💣 Nuking dev environment...")

  if command.include_data:
    shutil.rmtree(BUCKETS_DIR,ignore_errors=True)
    shutil.rmtree(RECEIPTS_DIR,ignore_errors=True)

  result = subprocess.run(["docker", "compose", "down", "--rm"], )
  result = subprocess.run(["docker", "compose", "kill"])

  print("✅ Dev environment nuked.")
