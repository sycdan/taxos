import os

from dev import REPO_ROOT
from dev.build.image.command import BuildImage


def gen_proto():
  from dev.build.proto.command import BuildProto

  BuildProto().execute()


def build_image():
  print("Building Docker image...")
  os.chdir(REPO_ROOT)
  if os.system("docker compose build"):
    raise RuntimeError("docker compose build failed")


def handle(command: BuildImage):
  if not command.no_proto:
    gen_proto()
  if not command.no_docker:
    build_image()
