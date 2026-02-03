import os

from dev.up.command import Up


def handle(command: Up):
  if command.build:
    os.system("docker compose build")
  try:
    os.system("docker compose up" + (" --watch" if not command.no_watch else ""))
  except KeyboardInterrupt:
    os.system("docker compose down")
