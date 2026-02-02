import os
from dev.up.command import Up

def handle(command: Up):
  """Handle the up command."""
  try:
    os.system("docker compose up" + (" --watch" if not command.no_watch else ""))
  except KeyboardInterrupt:
    os.system("docker compose down")
