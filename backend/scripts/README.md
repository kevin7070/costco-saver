# Dev scripts

Local development helpers. **Not for production.** All commands are run from the
repo root with the docker stack up.

## seed_dev.py — seed test accounts (idempotent)

Creates one admin + three regular users. Safe to re-run (uses `get_or_create`).

```sh
docker compose exec -T web python manage.py shell < backend/scripts/seed_dev.py
```

| Email | Password | Role |
|-------|----------|------|
| `test@costco.local` | `TestPass123!` | admin (staff + superuser) |
| `user@costco.local` | `UserPass123!` | user |
| `user2@costco.local` | `UserPass123!` | user |
| `user3@costco.local` | `UserPass123!` | user |

## reset-dev.sh — flush data + re-seed

Wipes ALL table data (`manage.py flush`, schema kept) then re-seeds the accounts
above. Use it to get back to a clean slate between tests.

```sh
bash backend/scripts/reset-dev.sh
```

For a full schema rebuild (e.g. after a destructive migration change):

```sh
docker compose down -v && docker compose up -d --build
```
