#!/bin/sh
set -e

# Run database migrations before starting the server.
# Using `set -e` ensures the container exits immediately if migrations fail.
echo "Running database migrations..."
alembic upgrade head

# Bind the port from the environment. BACKEND_PORT is the project-wide
# convention (config.py, docker-compose*.yml); fall back to PORT for platforms
# that inject it (e.g. Render), then to 8000.
BACKEND_PORT="${BACKEND_PORT:-${PORT:-8000}}"
echo "Starting server on port ${BACKEND_PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}"
