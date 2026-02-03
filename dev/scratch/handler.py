import os

from dev.scratch.command import Scratch


def handle(command: Scratch):
  os.system("docker compose build")
  os.system("docker run -it --rm taxos-backend bash")
