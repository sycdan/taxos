# Start a tmux server if none exists
if ! tmux has-session 2>/dev/null; then
  echo "Starting tmux server..."
  tmux new-session -d -s taxos
fi

# Kill old server window if it exists
tmux kill-window -t server 2>/dev/null || true

# Create a fresh server window
tmux new-window -n server "scaf /workspaces/taxos --call dev/serve"
