# Single image, four roles (web / worker / receipt-worker / beat) — see docker-compose.yml
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Playwright Firefox + its system deps, for costco.ca price scraping.
# Firefox evades Akamai-style bot detection far more reliably than Chromium.
RUN playwright install --with-deps firefox

COPY . .

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
