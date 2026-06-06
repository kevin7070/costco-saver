# Costco Saver

Keep track of what you bought at Costco and get alerted when the price drops
while you can still claim the difference.

Create an account and upload a receipt to get started.

> 🚧 Early development (v0.5.0).

## What it does

- **Receipt capture** — upload a receipt (image or PDF); it is parsed into line
  items for you to review and confirm.
- **Price tracking** — confirmed products are matched by item number and tracked
  over time.
- **Drop alerts** — when a tracked product's price falls below what you paid, an
  alert is raised, flagged for whether it is still within the price-adjustment
  window.

Price lookups go through a pluggable provider; the bundled default is a no-op, so
a real price source is supplied by the deployment environment.

Accounts are protected with email verification, password reset, and optional
two-factor authentication (TOTP).

## Stack

Django + DRF (backend) · Next.js + Tailwind (frontend) · PostgreSQL · Celery / Redis.
Monorepo: `backend/` + `frontend/`.

## Development

```bash
git clone https://github.com/kevin7070/costco-saver.git
cd costco-saver
cp backend/.env.example backend/.env   # then fill in secrets
docker compose up --build
```

An Apache vhost reverse-proxies the published frontend port.
