#!/bin/bash
set -e

# Dev-specific env setup
if [ -f /workspaces/taxos/bootstrap.sh ]; then
  source /workspaces/taxos/bootstrap.sh
fi

# Ensure .venvrc is sourced in interactive shells
if ! grep -q 'source /workspaces/taxos/.venvrc' ~/.bashrc 2>/dev/null; then
  echo "source /workspaces/taxos/.venvrc" >> ~/.bashrc
fi

# Fix docker socket permissions so vscode user can connect
sudo chmod 666 /var/run/docker.sock 2>/dev/null || true

# Seed dev data (idempotent)
cd /workspaces/taxos
scaf call dev/seed || true

exec "$@"
