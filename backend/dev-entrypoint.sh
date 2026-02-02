#!/bin/bash

# Generate protobuf files if they don't exist or proto files are newer
if [ ! -f "taxos_service_pb2.py" ] || [ "protos/taxos_service.proto" -nt "taxos_service_pb2.py" ]; then
  echo "Generating protobuf files..."
  python -m grpc_tools.protoc \
  --proto_path=protos \
  --python_out=. \
  --grpc_python_out=. \
  protos/taxos_service.proto
  echo "Protobuf files generated."
fi

# Start the server with hot reload
exec python -m watchdog.watchmedo auto-restart --patterns=*.py --recursive -- python server.py