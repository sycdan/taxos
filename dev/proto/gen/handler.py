import os

from dev import PROTO_DIR
from dev.proto.gen.command import GenProto


def handle(command: GenProto):
  print("Generating protos...")
  os.chdir(PROTO_DIR)
  if os.system("buf generate"):
    raise RuntimeError("buf generate failed")
