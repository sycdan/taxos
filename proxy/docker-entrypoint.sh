#!/bin/sh
set -e

# Substitute environment variables in nginx config
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Execute the main command
exec "$@"