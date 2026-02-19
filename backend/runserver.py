"""Dev-mode entrypoint.

Debugpy is injected by Dockerfile.dev via `python -m debugpy`, so this file
just starts the app. Hot reload is provided by Flask's built-in reloader:
any file change that lands in the container (via the bind mount) causes the
server to restart automatically — no container restart needed.

To debug: use the "Backend: Attach Debugger" launch config in VS Code.
"""

import api.connect_http_server as server

server.main()

