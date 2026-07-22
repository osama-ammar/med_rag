#!/bin/bash
set -e

echo "Running database migrations..."
cd /app/models/db_schemes/minirag/
alembic upgrade head

# Return to the app root
cd /app

echo "Starting FastAPI server..."
# The 'exec' command is critical here to keep the process alive
export PYTHONPATH=$PYTHONPATH:/app
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000

