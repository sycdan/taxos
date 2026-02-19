FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends procps gdb \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir debugpy

COPY sidecar.py /sidecar.py

CMD ["python", "/sidecar.py"]
