if command -v tmux >/dev/null && [ -z "$TMUX" ]; then
  tmux attach -t taxos || tmux new -s taxos
fi
