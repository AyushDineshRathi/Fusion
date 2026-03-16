#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-Fusion.settings.development}"
export DATABASE_HOST="${DATABASE_HOST:-${DB_HOST:-postgres}}"
export DATABASE_PORT="${DATABASE_PORT:-5432}"

echo "Waiting for PostgreSQL at ${DATABASE_HOST}:${DATABASE_PORT}..."
python - <<'PY'
import os
import socket
import time

host = os.environ["DATABASE_HOST"]
port = int(os.environ["DATABASE_PORT"])

for attempt in range(1, 61):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"PostgreSQL is reachable on attempt {attempt}.")
            break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL did not become reachable in time.")
PY

# Apply database migrations
echo "Apply database migrations"
python FusionIIIT/manage.py migrate --noinput

# Start server
echo "Starting server"
python FusionIIIT/manage.py runserver 0.0.0.0:8000
