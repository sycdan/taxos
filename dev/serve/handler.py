import os

from dev.serve.command import Serve


def handle(command: Serve):
  try:
    os.system("docker compose up" + (" --watch" if not command.no_watch else ""))
  except KeyboardInterrupt:
    os.system("docker compose down")
