#!/usr/bin/env bash
#
# Reset the local dev database: flush ALL data, then re-seed test accounts.
# LOCAL / DEV ONLY. Runnable from anywhere (it anchors itself to the repo root):
#
#     bash backend/scripts/reset-dev.sh      # or  ./backend/scripts/reset-dev.sh
#
# `flush` wipes table data but keeps the schema/migrations (no re-migrate); we
# also delete uploaded media files so receipt images / avatars don't orphan.
# This is a fast "clean slate + test accounts" reset, not a teardown.
# For a full schema rebuild, use: docker compose down -v && docker compose up -d --build
set -euo pipefail

# Anchor to the repo root so `docker compose` finds the project and the
# seed-script redirect below resolves no matter where this is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

echo "⚠️  Flushing ALL data in the dev database..."
docker compose exec -T web python manage.py flush --no-input

echo "Deleting uploaded media files (receipts, avatars)..."
# -mindepth 1 keeps /app/media (the volume mount) itself; deletes its contents.
docker compose exec -T web find /app/media -mindepth 1 -delete

echo "Seeding dev/test accounts..."
docker compose exec -T web python manage.py shell < backend/scripts/seed_dev.py

echo "✓ Reset complete — test accounts re-seeded (see backend/scripts/README.md)."
