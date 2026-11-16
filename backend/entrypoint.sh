#!/bin/sh
set -e

# Apply schema migrations on boot (safe to run repeatedly).
python manage.py migrate --noinput

# Optionally create/refresh the demo account so a fresh deployment has data to explore.
if [ "${SEED_DEMO:-false}" = "true" ]; then
  python manage.py seed_demo
fi

exec "$@"
