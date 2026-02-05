import os

from dev import PROTO_DIR
from dev.proto.gen.command import GenProto


def gen_proto():
  print("Generating protos...")
  os.chdir(PROTO_DIR)
  if os.system("buf generate"):
    raise RuntimeError("buf generate failed")


def handle(command: GenProto):
  gen_proto()
