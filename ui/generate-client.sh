#!/bin/bash
set -e

# Create generated directory
mkdir -p src/api/generated

# Generate TypeScript code from proto files
npx protoc \
--plugin=protoc-gen-ts=./node_modules/.bin/protoc-gen-ts \
--ts_out=src/api/generated \
--proto_path=../backend/protos \
../backend/protos/taxos_service.proto

echo "✅ TypeScript client code generated successfully!"