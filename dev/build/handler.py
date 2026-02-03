import os
import sys
from importlib.resources import files
from os import makedirs
from pathlib import Path

from grpc_tools import protoc

from dev import BACKEND_ROOT, FRONTEND_ROOT, PROTO_DIR, REPO_ROOT
from dev.build.command import Build

WKT_DIR = str(files("grpc_tools").joinpath("_proto"))


def gen_backend():
  print("Generating backend protos...")
  os.chdir(REPO_ROOT)

  py_out = (BACKEND_ROOT / "api").relative_to(REPO_ROOT)
  makedirs(py_out.as_posix(), exist_ok=True)

  for proto in PROTO_DIR.rglob("*.proto"):
    proto_file = proto.relative_to(PROTO_DIR)
    print(f"Compiling {proto_file} -> {py_out}...")

    protoc.main(
      [
        "protoc",
        f"--proto_path={WKT_DIR}",
        f"--proto_path={PROTO_DIR.as_posix()}",
        f"--pyi_out={py_out.as_posix()}",
        f"--python_out={py_out.as_posix()}",
        f"--grpc_python_out={py_out.as_posix()}",
        proto.as_posix(),
      ]
    )


def gen_frontend():
  print("Generating frontend protos...")
  os.chdir(REPO_ROOT)

  ts_out = (FRONTEND_ROOT / "src" / "api").relative_to(REPO_ROOT)
  makedirs(ts_out, exist_ok=True)

  for proto in PROTO_DIR.rglob("*.proto"):
    proto_file = proto.relative_to(PROTO_DIR)
    print(f"Compiling {proto_file} -> {ts_out}...")

    result = protoc.main(
      [
        "protoc",
        f"--proto_path={WKT_DIR}",
        f"--proto_path={PROTO_DIR.as_posix()}",
        f"--es_out={ts_out.as_posix()}",
        proto.relative_to(PROTO_DIR).as_posix(),
      ]
    )
    if result:
      print(f"Failed to compile {proto_file}", file=sys.stderr)


def handle(command: Build):
  if not command.no_backend:
    gen_backend()
  if not command.no_frontend:
    gen_frontend()
  if not command.no_docker:
    os.system("docker compose build")
