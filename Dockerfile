FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY backend/ .

# Collect static files (needed for Django admin).
# Use a throwaway SECRET_KEY — the real one comes from env at runtime.
RUN DJANGO_SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

EXPOSE 8000

# Gunicorn with 2 workers — tune via WEB_CONCURRENCY env var in production.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
