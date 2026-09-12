#!/bin/sh
set -e

# Development keeps the convenient migration-on-start behaviour. Production
# runs migrations through the updater's one-shot service after a verified backup.
if [ "${BACKEND_AUTO_MIGRATE:-true}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
fi

# Bind the port from the environment. BACKEND_PORT is the project-wide
# convention (config.py, docker-compose*.yml); fall back to PORT for platforms
# that inject it (e.g. Render), then to 8000.
BACKEND_PORT="${BACKEND_PORT:-${PORT:-8000}}"
echo "Starting server on port ${BACKEND_PORT}..."
if [ "${BACKEND_DEBUG:-false}" = "true" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" --reload
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}"
