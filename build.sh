#!/bin/bash
set -e

echo "🏗️ Building Taxos Backend and UI..."

# Navigate to project root
cd "$(dirname "$0")"

# Create data directory if it doesn't exist
mkdir -p data

# Build and push backend
echo "📦 Building backend..."
cd backend
docker build -t htpc.lan:5000/taxos-backend:latest .
docker push htpc.lan:5000/taxos-backend:latest
cd ..

# Build and push UI
echo "🎨 Building UI..."
cd ui
# Install dependencies and generate gRPC client code
npm install
npm run generate:client
docker build -t htpc.lan:5000/taxos-ui:latest .
docker push htpc.lan:5000/taxos-ui:latest
cd ..

echo "✅ Build complete! You can now run: docker compose up"