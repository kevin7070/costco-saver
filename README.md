# Costco Saver

A tool to help save money at Costco.

> 🚧 Early development.

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
