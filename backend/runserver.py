"""Development only"""

import debugpy

DEBUG_ADDR = ("0.0.0.0", 5678)

if not debugpy.is_client_connected():
  try:
    debugpy.listen(DEBUG_ADDR)
    print(f"Debugger listening on {DEBUG_ADDR[1]}")
  except Exception as e:
    print(f"Debugger already active or port in use: {e}")

# Optional: wait for VS Code only if we successfully started listening
if not debugpy.is_client_connected():
  print("Waiting for debugger attach...")
  debugpy.wait_for_client()

import api.connect_http_server as server

server.main()
