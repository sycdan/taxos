import os
from importlib.resources import files
from os import makedirs
from pathlib import Path

from grpc_tools import protoc
from taxos import ROOT_DIR

from dev.build.command import Build

WKT_DIR = str(files("grpc_tools").joinpath("_proto"))


def gen_backend(proto_dir: Path):
  py_out = ROOT_DIR / "api"
  makedirs(py_out.as_posix(), exist_ok=True)
  for proto in proto_dir.rglob("*.proto"):
    protoc.main(
      [
        "protoc",
        f"--proto_path={WKT_DIR}",
        f"--proto_path={proto_dir.as_posix()}",
        f"--pyi_out={py_out.as_posix()}",
        f"--python_out={py_out.as_posix()}",
        f"--grpc_python_out={py_out.as_posix()}",
        proto.as_posix(),
      ]
    )


def gen_frontend(proto_dir: Path):
  ts_out = ROOT_DIR / "ui" / "src"
  makedirs(ts_out.as_posix(), exist_ok=True)
  for proto in proto_dir.rglob("*.proto"):
    protoc.main(
      [
        "protoc",
        f"--proto_path={WKT_DIR}",
        f"--proto_path={proto_dir.as_posix()}",
        f"--es_out={ts_out.as_posix()}",
        "--es_opt=target=ts",
        f"--connect-es_out={ts_out.as_posix()}",
        "--connect-es_opt=target=ts",
        proto.as_posix(),
      ]
    )


def handle(command: Build):
  proto_dir = ROOT_DIR / "protos"
  if not command.no_backend:
    gen_backend(proto_dir)
  if not command.no_frontend:
    gen_frontend(proto_dir)
  if not command.no_docker:
    os.system("docker compose build")
