import os

from dev.serve.command import Serve


def handle(command: Serve):
  cmd_parts = ["PYTHONPATH=backend python"]
  if not command.no_debug:
    cmd_parts.append("-m debugpy --listen 5678")
  cmd_parts.append("backend/api/connect_http_server.py")
  try:
    os.system(" ".join(cmd_parts))
  except KeyboardInterrupt:
    pass
