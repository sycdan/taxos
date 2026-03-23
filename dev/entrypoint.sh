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

# Install git hooks
HOOKS_SRC="/workspaces/taxos/dev/git/hooks"
HOOKS_DST="/workspaces/taxos/.git/hooks"
for hook in "$HOOKS_SRC"/*; do
  hook_name="$(basename "$hook")"
  ln -sf "$hook" "$HOOKS_DST/$hook_name"
  chmod +x "$HOOKS_DST/$hook_name"
done

# Seed dev data
cd /workspaces/taxos
scaf call dev/seed || true

exec "$@"
