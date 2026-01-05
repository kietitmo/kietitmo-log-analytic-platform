#!/bin/sh
set -e

if [ "$ENV" = "dev" ] && [ "$INIT_USERS" = "true" ]; then
    python /app/app/scripts/init_users.py
    echo "Initialized default users."
fi

exec "$@"
