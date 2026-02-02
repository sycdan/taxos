#!/bin/bash
# Development environment helper script

case "$1" in
  "dev")
    echo "🚀 Starting development environment..."
    docker compose -f docker-compose.dev.yml up --build
  ;;
  "watch")
    echo "🔄 Starting with file watching..."
    docker compose -f docker-compose.dev.yml watch
  ;;
  "down")
    echo "🛑 Stopping development environment..."
    docker compose -f docker-compose.dev.yml down
  ;;
  "logs")
    echo "📋 Showing logs for service: ${2:-all}"
    if [ -n "$2" ]; then
      docker compose -f docker-compose.dev.yml logs -f "$2"
    else
      docker compose -f docker-compose.dev.yml logs -f
    fi
  ;;
  "build")
    echo "🏗️ Rebuilding services..."
    docker compose -f docker-compose.dev.yml build
  ;;
  "clean")
    echo "🧹 Cleaning up development environment..."
    docker compose -f docker-compose.dev.yml down -v
    docker system prune -f
  ;;
  *)
    echo "TaxOS Development Helper"
    echo ""
    echo "Usage: $0 {dev|watch|down|logs|build|clean}"
    echo ""
    echo "Commands:"
    echo "  dev     - Start development environment"
    echo "  watch   - Start with Docker Compose watch for hot reloading"
    echo "  down    - Stop development environment"
    echo "  logs    - Show logs (add service name as second argument)"
    echo "  build   - Rebuild all services"
    echo "  clean   - Stop and clean up everything"
    echo ""
    echo "Examples:"
    echo "  $0 dev                    # Start all services"
    echo "  $0 watch                  # Start with file watching"
    echo "  $0 logs taxos-ui-dev      # Show UI logs"
    echo "  $0 down                   # Stop everything"
  ;;
esac