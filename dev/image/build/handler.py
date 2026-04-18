import os
import datetime as dt

from image.build.command import BuildImage

from dev import BACKEND_ROOT, FRONTEND_ROOT

DATE_VERSION = dt.datetime.now().strftime("%Y%m%d%H%M%S")
REGISTRY = "htpc.lan:5000"
BACKEND_IMAGE = f"{REGISTRY}/taxos-backend:{DATE_VERSION}"
FRONTEND_IMAGE = f"{REGISTRY}/taxos-frontend:{DATE_VERSION}"
BACKEND_LATEST = f"{REGISTRY}/taxos-backend:latest"
FRONTEND_LATEST = f"{REGISTRY}/taxos-frontend:latest"


def build_image():
  print("Building backend image...")
  os.chdir(BACKEND_ROOT)
  if os.system(f"docker build -t {BACKEND_IMAGE} -t {BACKEND_LATEST} ."):
    raise RuntimeError("backend build failed")
  os.chdir(FRONTEND_ROOT)
  if os.system(f"docker build -t {FRONTEND_IMAGE} -t {FRONTEND_LATEST} ."):
    raise RuntimeError("frontend build failed")


def push_image():
  os.system(f"docker push {BACKEND_IMAGE}")
  os.system(f"docker push {BACKEND_LATEST}")
  os.system(f"docker push {FRONTEND_IMAGE}")
  os.system(f"docker push {FRONTEND_LATEST}")


def handle(command: BuildImage):
  build_image()
  if not command.no_push:
    push_image()

  print("To deploy, copy docker-compose.production.yml to target machine and run:")
  print("docker compose -f docker-compose.production.yml up -d")
