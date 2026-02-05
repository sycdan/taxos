import os

from dev import PROTO_DIR, REPO_ROOT
from dev.build.command import Build


def gen_proto():
  print("Generating protos...")
  os.chdir(PROTO_DIR)
  if os.system("buf generate"):
    raise RuntimeError("buf generate failed")


def build_image():
  print("Building Docker image...")
  os.chdir(REPO_ROOT)
  if os.system("docker compose build"):
    raise RuntimeError("docker compose build failed")


def handle(command: Build):
  if not command.no_proto:
    gen_proto()
  if not command.no_docker:
    build_image()
