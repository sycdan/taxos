import os

from dev.test_api.command import TestApi


def handle(command: TestApi, *args):
  cmd_args = ["pytest", "--no-header", "--verbose", "backend"]
  cmd_args.extend(args)
  if not command.no_integration:
    cmd_args.append("--run-integration")
  os.system(" ".join(cmd_args))
