# FeatureVote

Full-stack feature voting system. Users submit feature requests, browse what others have proposed, upvote the ones they care about, and see everything ranked by popularity. Built with Django, React, and Supabase Postgres.

## Architecture

```
React (Vite + TypeScript)  →  Django REST Framework  →  Supabase Postgres
         ↑                            ↑                        ↑
   TanStack Query              sole API backend          managed database
   Tailwind CSS v4            session middleware          standard Postgres
   Zod validation             DRF serializers             no vendor lock-in
   Plus Jakarta Sans          13 automated tests
```

Every data operation flows through Django. The React app never touches Supabase directly — no client SDK, no direct queries, no split authority over data. One backend, one source of truth.

### Why this stack

**Supabase as managed Postgres.** Supabase gives us a production-ready Postgres instance with zero ops — connection pooling, backups, and a dashboard included. But we treat it strictly as a database. Django connects via a standard `DATABASE_URL` through `psycopg2`. No Supabase client libraries exist anywhere in this project. If we swapped Supabase for any other Postgres host, the only change is an environment variable.

**Django as the application backend.** All business logic — vote integrity, one-vote-per-user enforcement, ranking, validation — lives in Django. DRF handles serialization, content negotiation, and error formatting. This keeps the frontend thin and the invariants centralized. Moving logic into the React layer or splitting it across Supabase RPCs would create two places to enforce the same rules.

**Responsive PWA instead of a native mobile app.** The assignment requires web and mobile accessibility. A separate React Native or Flutter app doubles the surface area for a take-home with no proportional gain. Instead: mobile-first Tailwind layout that works well at every breakpoint, plus a PWA manifest and service worker for home-screen installability. One codebase, both platforms, zero build toolchain overhead.

## Key Features

- **Submit feature requests** with title and description, validated on both client (Zod) and server (DRF serializers)
- **Upvote and un-vote** with a single click — toggle behavior, optimistic UI updates, server reconciliation
- **Ranked list** ordered by vote count, tiebroken by recency — backed by a B-tree index on `vote_count`
- **Vote integrity** enforced at the Postgres level: `UniqueConstraint(voter, feature_request)` prevents duplicates even under concurrent requests
- **Self-vote prevention** — you cannot upvote your own submission
- **Anonymous session identity** — a UUID generated in the browser and sent as `X-Session-Id` on every request, mapped to a `Voter` row server-side
- **Optimistic updates** via TanStack Query mutations with rollback on failure
- **Accessible** — WCAG focus-visible indicators, aria-labels, aria-live regions, reduced-motion support
- **Responsive** — mobile-first layout with breakpoints at sm/md/lg, 44px touch targets
- **PWA installable** on mobile and desktop

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv

# Activate the virtual environment
source venv/bin/activate        # macOS / Linux
source venv/Scripts/activate    # Windows (Git Bash)

pip install -r requirements.txt
cp .env.example .env            # Edit .env if connecting to Supabase (see below)
python manage.py migrate
python manage.py seed_demo      # Populate 8 realistic features with votes
python manage.py runserver
```

API runs at `http://localhost:8000/api/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173/`. Vite proxies `/api/*` to Django automatically.

### Environment Variables

All configured in `backend/.env`. Copy from `.env.example` to start.

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DATABASE_URL` | No | SQLite | Postgres connection string. Omit for local SQLite. For Supabase: find under Project Settings → Database → Connection string (URI, session mode, port 5432). |
| `DJANGO_SECRET_KEY` | Yes (prod) | dev fallback | Standard Django secret key. |
| `DEBUG` | No | `True` | Set `False` in production. |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated. |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:5173` | Comma-separated origins allowed to call the API. |

To run against Supabase Postgres, set `DATABASE_URL` to your connection string and re-run `migrate` and `seed_demo`. Everything else stays the same.

## API

| Method | Endpoint | Description | Success | Key Errors |
|--------|----------|-------------|---------|------------|
| `GET` | `/api/features/` | List all features, ranked by votes | `200` | `401` missing header, `400` malformed UUID |
| `POST` | `/api/features/` | Create a feature request | `201` | `401` missing header, `400` validation |
| `POST` | `/api/features/{id}/vote/` | Upvote a feature | `201` | `403` self-vote, `409` duplicate |
| `DELETE` | `/api/features/{id}/vote/` | Remove your upvote | `200` | `404` not voted |

All endpoints require the `X-Session-Id: <uuid>` header. Missing → `401`, malformed → `400`. The frontend handles this transparently via `crypto.randomUUID()` stored in localStorage.

## Data Model

```
Voter
  id              UUID (PK)
  session_id      CharField(64), unique, indexed
  created_at      DateTimeField

FeatureRequest
  id              UUID (PK)
  title           CharField(200)
  description     TextField
  author          FK → Voter
  vote_count      PositiveIntegerField, indexed    ← denormalized for O(1) ranking
  created_at      DateTimeField
  updated_at      DateTimeField
  ── CHECK vote_count >= 0

Vote
  id              UUID (PK)
  voter           FK → Voter
  feature_request FK → FeatureRequest
  created_at      DateTimeField
  ── UNIQUE (voter, feature_request)
```

## Tests

```bash
cd backend
python manage.py test features.tests -v2
```

13 tests across 5 classes, all passing:

| Class | Tests | What it proves |
|-------|-------|----------------|
| `VoteIntegrityTests` | 3 | Duplicate vote → 409, self-vote → 403, unvote without vote → 404 |
| `VoteCountTests` | 3 | Vote increments to 1, unvote decrements to 0, two voters yield count of 2 (all verified via `refresh_from_db`) |
| `MiddlewareAndSerializerTests` | 4 | Missing header → 401, malformed UUID → 400, spoofed `author` field ignored, injected `vote_count` ignored |
| `RankingTests` | 2 | Features returned in descending vote order, tiebroken by most recent first (asserted on id order) |
| `RaceConditionTests` | 1 | Two threads fire simultaneously via `threading.Barrier` — exactly one 201, one 409, one Vote row, `vote_count` = 1. Skipped on SQLite (shared-cache ignores busy_timeout); runs on Postgres. |

## Technical Decisions

| Decision | What and why |
|----------|-------------|
| **Denormalized `vote_count`** | Avoids `COUNT(*)` JOIN on every list query. Updated atomically inside `transaction.atomic()` using `F("vote_count") + 1`. The `CheckConstraint` prevents it from going negative. |
| **`UniqueConstraint` on Vote** | One-vote-per-user-per-feature enforced at the database level. If a race condition hits the application check, the constraint catches it and the view returns `409`. |
| **Anonymous session identity** | Full auth adds login UI, token management, and password flows — none of which improve the core product for a time-boxed submission. A UUID in localStorage demonstrates the same vote-integrity mechanics. The `Voter` model is a thin shim; replacing it with a real `User` FK is a one-migration change. |
| **Separate read/write serializers** | `FeatureRequestListSerializer` includes viewer-specific computed fields (`has_voted`, `is_own`). `FeatureRequestCreateSerializer` accepts only `title` and `description` — the `author` is set from `request.voter` server-side, not from client input. |
| **Batch `has_voted` resolution** | The list view fetches the voter's voted feature IDs in a single query, then passes the set into serializer context. This avoids N+1 queries — one DB hit instead of one per card. |
| **Explicit `order_by` in the view** | Ranking is `ORDER BY -vote_count, -created_at`, stated at the call site rather than buried in `Meta.ordering`. The `db_index` on `vote_count` lets Postgres satisfy this without a filesort. |
| **No signals for vote count** | Vote count updates happen inline in the vote/unvote view, wrapped in `transaction.atomic()`. Signals fail silently, run outside the request's transaction, and obscure the data flow. Inline updates are explicit and testable. |
| **Middleware UUID validation** | `X-Session-Id` is validated against a UUID regex before hitting the database. Rejects garbage input at the boundary instead of creating junk `Voter` rows. |
| **PWA over native mobile** | A service worker and web manifest get us home-screen installability. The Tailwind layout is mobile-first. This ships in minutes and covers the "accessible on mobile" requirement without a second codebase. |
| **No pagination** | With fewer than 1,000 expected items for a demo, pagination adds routing and state complexity with no user-facing benefit. Listed as a next step. |

## Project Structure

```
├── backend/
│   ├── config/                  # Django settings, root URL config
│   │   ├── settings.py          # DATABASE_URL, CORS, DRF config
│   │   └── urls.py
│   ├── features/                # Single Django app — all domain logic
│   │   ├── models.py            # Voter, FeatureRequest, Vote
│   │   ├── views.py             # list/create, vote/unvote
│   │   ├── serializers.py       # read + write serializers
│   │   ├── middleware.py        # X-Session-Id → Voter resolution
│   │   ├── urls.py              # /api/features/, /api/features/{id}/vote/
│   │   ├── tests.py             # 13 tests across 5 classes
│   │   ├── admin.py             # Django admin registration
│   │   └── management/commands/
│   │       └── seed_demo.py     # Realistic demo data
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # Header, SubmitForm, FeatureList, FeatureCard, VoteButton, EmptyState
│   │   ├── hooks/               # useFeatures (query), useVote (mutations + optimistic updates)
│   │   ├── lib/                 # api.ts (fetch wrapper), session.ts (UUID), schemas.ts (Zod)
│   │   ├── App.tsx
│   │   └── main.tsx             # QueryClientProvider, service worker registration
│   ├── public/                  # manifest.json, sw.js, favicon.svg
│   ├── package.json
│   └── vite.config.ts           # Tailwind plugin, /api proxy to Django
└── README.md
```

## What I'd Build Next (4–8 hours)

- **Real authentication** — swap the `Voter` shim for Django's `User` model, add a lightweight OAuth or magic-link login flow, replace `X-Session-Id` with token-based auth
- **Cursor pagination** — keyset pagination on `(vote_count, created_at)` for infinite scroll without offset drift
- **Status labels** — let admins tag features as Planned / In Progress / Shipped to close the feedback loop
- **Search and filtering** — full-text search on title and description via Postgres `tsvector`, filter by status or date range
- **WebSocket vote updates** — Django Channels to push vote count changes to all connected clients in real time
- **Rate limiting** — throttle feature creation and vote toggling per session to prevent abuse
- **Dark mode** — Tailwind's `dark:` variant with system preference detection and manual toggle
- **Production deployment** — Dockerize both services, add a GitHub Actions CI pipeline, deploy frontend to Vercel and backend to Railway or Fly.io
