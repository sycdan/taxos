#!/bin/bash

# Build and Push Script for Taxos App
# Usage: ./build-and-push.sh

set -e

REGISTRY="htpc.lan:5000"
BACKEND_IMAGE="$REGISTRY/taxos-backend:latest"
FRONTEND_IMAGE="$REGISTRY/taxos-frontend:latest"

echo "Building backend image..."
docker build -t $BACKEND_IMAGE -f backend/Dockerfile backend

echo "Building frontend image..."
docker build -t $FRONTEND_IMAGE -f frontend/Dockerfile frontend

echo "Pushing backend image..."
docker push $BACKEND_IMAGE

echo "Pushing frontend image..."
docker push $FRONTEND_IMAGE

echo "Images built and pushed successfully!"
echo "Backend: $BACKEND_IMAGE"
echo "Frontend: $FRONTEND_IMAGE"
echo ""
echo "To deploy on target machine, copy docker-compose.prod.yml and run:"
echo "docker-compose -f docker-compose.prod.yml up -d"