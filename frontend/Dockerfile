# Multi-stage. Default target is `runner` (the last stage) so a plain
# `docker build` / base compose still produces the production standalone image.
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Dev stage: full deps + Next dev server with Fast Refresh (HMR). Selected only by
# the local docker-compose override (target: dev) for iteration; source is
# bind-mounted at runtime, so edits hot-reload without an image rebuild.
FROM node:20-slim AS dev
WORKDIR /app
ENV NODE_ENV=development
COPY package*.json ./
RUN npm ci
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0", "-p", "3000"]

# Production runtime — MUST stay the last stage (it is the default build target).
FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
# Standalone bundle + static assets + public (standalone doesn't include these).
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
