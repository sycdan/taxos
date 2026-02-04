tmux kill-session -t server 2>/dev/null || true
tmux new-session -d -s server 'PYTHONPATH=backend python -m debugpy --listen 5678 backend/api/connect_http_server.py'
