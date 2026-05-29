#!/bin/sh

set -e

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 10000
