import os

from image.build.command import BuildImage
from proto.gen.command import GenProto

from dev import BACKEND_ROOT, FRONTEND_ROOT

REGISTRY = "htpc.lan:5000"
BACKEND_IMAGE = f"{REGISTRY}/taxos-backend:latest"
FRONTEND_IMAGE = f"{REGISTRY}/taxos-frontend:latest"


def build_image():
  print("Building backend image...")
  os.chdir(BACKEND_ROOT)
  if os.system(f"docker build -t {BACKEND_IMAGE} ."):
    raise RuntimeError("backend build failed")
  os.chdir(FRONTEND_ROOT)
  if os.system(f"docker build -t {FRONTEND_IMAGE} ."):
    raise RuntimeError("frontend build failed")


def push_image():
  os.system(f"docker push {BACKEND_IMAGE}")
  os.system(f"docker push {FRONTEND_IMAGE}")


def handle(command: BuildImage):
  if not command.no_proto:
    GenProto().execute()
  build_image()
  if not command.no_push:
    push_image()

  print("To deploy, copy docker-compose.production.yml to target machine and run:")
  print("docker compose -f docker-compose.production.yml up -d")
