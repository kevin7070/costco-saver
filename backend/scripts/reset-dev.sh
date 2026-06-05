#!/usr/bin/env bash
#
# Reset the local dev database: flush ALL data, then re-seed test accounts.
# LOCAL / DEV ONLY. Run from the repo root:
#
#     bash backend/scripts/reset-dev.sh
#
# `flush` wipes table data but keeps the schema/migrations (no re-migrate),
# so this is a fast "clean slate + test accounts" reset, not a teardown.
# For a full schema rebuild, use: docker compose down -v && docker compose up -d --build
set -euo pipefail

echo "⚠️  Flushing ALL data in the dev database..."
docker compose exec -T web python manage.py flush --no-input

echo "Seeding dev/test accounts..."
docker compose exec -T web python manage.py shell < backend/scripts/seed_dev.py

echo "✓ Reset complete — test accounts re-seeded (see backend/scripts/README.md)."
