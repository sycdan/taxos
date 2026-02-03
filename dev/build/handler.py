import shutil
from os import makedirs
from pathlib import Path

import pkg_resources
from grpc_tools import protoc
from taxos import ROOT_DIR

from dev.build.command import Build

WKT_DIR = pkg_resources.resource_filename("grpc_tools", "_proto")


def build_backend(proto_dir: Path):
  py_out = ROOT_DIR / "api" / "gen"
  shutil.rmtree(py_out, ignore_errors=True)
  makedirs(py_out.as_posix(), exist_ok=True)
  for proto in proto_dir.glob("*.proto"):
    protoc.main(
      [
        "protoc",
        f"--proto_path={WKT_DIR}",
        f"--proto_path={proto_dir.as_posix()}",
        f"--python_out={py_out.as_posix()}",
        f"--grpc_python_out={py_out.as_posix()}",
        proto.as_posix(),
      ]
    )


def build_frontend(proto_dir: Path):
  ts_out = ROOT_DIR / "ui" / "src" / "gen"
  shutil.rmtree(ts_out, ignore_errors=True)
  makedirs(ts_out.as_posix(), exist_ok=True)
  for proto in proto_dir.glob("*.proto"):
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
    build_backend(proto_dir)
  if not command.no_frontend:
    build_frontend(proto_dir)
