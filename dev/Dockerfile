# Python 3.14 devcontainer base — includes vscode user, sudo, git, pip, etc.
FROM mcr.microsoft.com/devcontainers/python:3.0.4-3.14-bookworm

# Install Node.js 20 (as root)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python requirements at build time so the container is ready immediately.
# Build context is the workspace root (see docker-compose.yml).
COPY backend/requirements.txt /tmp/backend-requirements.txt
COPY dev/requirements.txt /tmp/dev-requirements.txt
RUN pip install --no-cache-dir \
  -r /tmp/backend-requirements.txt \
  -r /tmp/dev-requirements.txt \
  && rm /tmp/backend-requirements.txt /tmp/dev-requirements.txt

# Copy and make entrypoint executable while still root
COPY dev/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to the vscode user for user-level tool installs
USER vscode

RUN mkdir -p /home/vscode/.local/bin

# Install Buf
RUN curl -sSL \
  "https://github.com/bufbuild/buf/releases/download/v1.34.0/buf-Linux-x86_64" \
  -o ~/.local/bin/buf \
  && chmod +x ~/.local/bin/buf

# Install grpcurl
RUN curl -sSL \
  https://github.com/fullstorydev/grpcurl/releases/download/v1.9.1/grpcurl_1.9.1_linux_x86_64.tar.gz \
  | tar -xz -C ~/.local/bin \
  && chmod +x ~/.local/bin/grpcurl

ENV PATH="/home/vscode/.local/bin:${PATH}"
ENV PYTHONPATH="/workspaces/taxos/backend:/workspaces/taxos/dev"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
