#!/bin/bash
set -e

# One-time user setup: clone dotfiles
if [ ! -d "$HOME/dotfiles" ]; then
  git clone https://github.com/sycdan/dotfiles.git ~/dotfiles \
    && bash ~/dotfiles/install.sh
fi

# Ensure .venvrc is sourced in interactive shells
if ! grep -q 'source /workspaces/taxos/.venvrc' ~/.bashrc 2>/dev/null; then
  echo "source /workspaces/taxos/.venvrc" >> ~/.bashrc
fi

# Seed dev data (idempotent)
cd /workspaces/taxos
scaf call dev/seed || true

exec "$@"

