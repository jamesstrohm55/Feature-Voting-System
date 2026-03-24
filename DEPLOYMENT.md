# Deployment Guide

## Architecture

```
Vercel (frontend)  →  Railway / Fly.io (backend)  →  Supabase (Postgres)
```

The frontend is a static SPA deployed to Vercel. The backend is a containerized Django app deployed to Railway or Fly.io. Supabase provides the managed Postgres database.

## Frontend — Vercel

### Setup

1. Connect the GitHub repo to Vercel
2. Set the root directory to `frontend`
3. Vercel auto-detects Vite — the `vercel.json` handles build config and SPA rewrites

### Environment

The frontend has no server-side env vars. The API base URL is `/api`, proxied in dev by Vite. In production, configure Vercel rewrites or set the API URL in the build:

| Variable | Value | Where |
|----------|-------|-------|
| `VITE_API_URL` | `https://your-backend.fly.dev` | Vercel → Settings → Environment Variables |

If using `VITE_API_URL`, update `frontend/src/lib/api.ts` to read `import.meta.env.VITE_API_URL` as the base URL. Alternatively, configure Vercel rewrites to proxy `/api/*` to the backend (avoids CORS entirely):

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://your-backend.fly.dev/api/:path*" }
  ]
}
```

## Backend — Railway or Fly.io

### Railway

1. Connect the GitHub repo
2. Set the root directory to `/` (Dockerfile is at project root)
3. Railway auto-detects the Dockerfile
4. Add environment variables in the Railway dashboard

### Fly.io

```bash
fly launch --dockerfile Dockerfile
fly secrets set DATABASE_URL="postgres://..." DJANGO_SECRET_KEY="..." ALLOWED_HOSTS="your-app.fly.dev" CORS_ALLOWED_ORIGINS="https://your-frontend.vercel.app"
fly deploy
```

### Environment Variables

| Variable | Example | Required |
|----------|---------|----------|
| `DATABASE_URL` | `postgres://postgres.[ref]:[pw]@aws-0-us-east-1.pooler.supabase.com:5432/postgres` | Yes |
| `DJANGO_SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` | Yes |
| `DEBUG` | `False` | Yes |
| `ALLOWED_HOSTS` | `your-app.fly.dev,your-app.up.railway.app` | Yes |
| `CORS_ALLOWED_ORIGINS` | `https://your-frontend.vercel.app` | Yes |

### Post-Deploy

Run migrations against the production database:

```bash
# Railway
railway run python manage.py migrate

# Fly.io
fly ssh console -C "python manage.py migrate"
```

Optionally seed demo data:

```bash
fly ssh console -C "python manage.py seed_demo"
```

## Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Go to Project Settings → Database → Connection string → URI
3. Use the **Session mode** connection string (port 5432)
4. Set this as `DATABASE_URL` in your backend deployment

No Supabase client libraries are used. Django connects via standard `psycopg2`. If you migrate away from Supabase, swap the `DATABASE_URL` to any Postgres host.

## CI

GitHub Actions runs on every push to `main`/`master` and on pull requests. The workflow:

1. Sets up Python 3.11
2. Installs backend dependencies
3. Runs migrations on SQLite (no Supabase needed in CI)
4. Runs all tests — build fails if any test fails

See `.github/workflows/ci.yml`.

## Production Checklist

- [ ] `DEBUG=False` on the backend
- [ ] Strong `DJANGO_SECRET_KEY` (not the dev fallback)
- [ ] `ALLOWED_HOSTS` set to your actual domain(s)
- [ ] `CORS_ALLOWED_ORIGINS` set to your Vercel domain
- [ ] `DATABASE_URL` pointing to Supabase Postgres
- [ ] Run `python manage.py migrate` on first deploy
- [ ] HTTPS enforced (Railway and Fly.io do this by default)
- [ ] Consider swapping LocMemCache for Redis if running multiple backend workers (rate limiting shares state)
