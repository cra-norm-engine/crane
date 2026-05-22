#!/bin/bash
set -e

cd /workspace/backend
echo "Running database migrations..."
python -m alembic upgrade head
echo "Migrations completed"

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
