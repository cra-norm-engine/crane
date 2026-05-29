#!/bin/sh
set -e

# Run database migrations before starting the server.
# Using `set -e` ensures the container exits immediately if migrations fail.
echo "Running database migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
