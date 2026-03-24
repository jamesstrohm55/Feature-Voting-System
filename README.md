# FeatureVote

Full-stack feature voting system with real authentication and role-based admin controls. Users register, log in, submit feature requests, browse what others have proposed, and upvote the ones they care about. Staff users manage status labels, pin important features, and moderate content. Everything is ranked by popularity with pinned features always at the top. Built with Django, React, and Supabase Postgres.

**Live:** [feature-voting-system.vercel.app](https://feature-voting-system.vercel.app)

## Architecture

```
React (Vite + TypeScript)  →  Django REST Framework  →  Supabase Postgres
         ↑                            ↑                        ↑
   TanStack Query              sole API backend          managed database
   Tailwind CSS v4             TokenAuthentication        standard Postgres
   Zod validation              role-based permissions     no vendor lock-in
   Plus Jakarta Sans           41 automated tests
```

**Auth flow:**
1. User registers or logs in via `POST /api/auth/register/` or `/api/auth/login/`
2. Server returns a DRF `Token` — stored in localStorage on the client
3. Every subsequent request includes `Authorization: Token <key>` header
4. DRF's `TokenAuthentication` resolves the token to a `User` on every request
5. `IsAuthenticated` is the default permission — unauthenticated requests get `401`
6. Staff-only endpoints check `request.user.is_staff` — non-staff gets `403`

Every data operation flows through Django. The React app never touches Supabase directly — no client SDK, no direct queries, no split authority over data. One backend, one source of truth.

### Why this stack

**Supabase as managed Postgres.** Supabase gives us a production-ready Postgres instance with zero ops — connection pooling, backups, and a dashboard included. But we treat it strictly as a database. Django connects via a standard `DATABASE_URL` through `psycopg2`. No Supabase client libraries exist anywhere in this project. If we swapped Supabase for any other Postgres host, the only change is an environment variable.

**Django as the application backend.** All business logic — authentication, vote integrity, one-vote-per-user enforcement, ranking, role-based permissions, validation — lives in Django. DRF handles serialization, content negotiation, token auth, and error formatting. This keeps the frontend thin and the invariants centralized. Moving logic into the React layer or splitting it across Supabase RPCs would create two places to enforce the same rules.

**Responsive PWA instead of a native mobile app.** The assignment requires web and mobile accessibility. A separate React Native or Flutter app doubles the surface area for a take-home with no proportional gain. Instead: mobile-first Tailwind layout that works well at every breakpoint, plus a PWA manifest and service worker for home-screen installability. One codebase, both platforms, zero build toolchain overhead.

## Key Features

- **Real authentication** — username/password registration and login via DRF TokenAuthentication. Tokens stored in localStorage, sent as `Authorization: Token <key>` on every request
- **Role-based permissions** — staff users (`is_staff=True`) get admin controls; regular users see a clean voting interface with no admin UI
- **Admin controls** — staff can update feature status (Under Review / Planned / In Progress / Shipped), pin features to the top, delete any feature or vote
- **Pinned features** — staff can pin important features; pinned items always rank above unpinned regardless of vote count, with a visual amber highlight for all users
- **Submit feature requests** with title and description, validated on both client (Zod) and server (DRF serializers)
- **Upvote and un-vote** with a single click — toggle behavior, optimistic UI updates, server reconciliation
- **Ranked list** ordered by pinned status, then vote count, then recency — backed by B-tree indexes on `is_pinned` and `vote_count`
- **Vote integrity** enforced at the Postgres level: `UniqueConstraint(user, feature_request)` prevents duplicates even under concurrent requests
- **Self-vote prevention** — you cannot upvote your own submission
- **Search** — server-side `?search=` query parameter filters by title and description (case-insensitive), combined with client-side status filtering
- **Status filtering** — client-side filter bar with five pills (All, Under Review, Planned, In Progress, Shipped)
- **Rate limiting** — 5 feature creates/hour and 30 votes/hour per user via DRF throttling, keyed on `user.pk`
- **Optimistic updates** via TanStack Query mutations with rollback on failure — for voting, status changes, pinning, and deletion
- **Accessible** — WCAG focus-visible indicators, aria-labels, aria-pressed, aria-live regions, reduced-motion support
- **Responsive** — mobile-first layout with breakpoints at sm/md/lg, 44px touch targets
- **PWA installable** on mobile and desktop

## Demo Accounts

The seed command creates two fixed accounts for local development and demos:

| Role | Username | Password | Permissions |
|------|----------|----------|-------------|
| Regular user | `testuser` | `testpass123` | Submit features, vote, search |
| Admin | `admin` | `adminpass123` | All of the above + update status, pin, delete features/votes (`is_staff=True`, `is_superuser=True`) |

> **These credentials are for local development only.** Do not use them in production. Generate strong passwords and rotate secrets on any deployed environment.

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
source venv\Scripts\activate.bat    # Windows (Git Bash)

pip install -r requirements.txt
cp .env.example .env            # Edit .env if connecting to Supabase (see below)
python manage.py migrate
python manage.py seed_demo      # Seeds 8 features, 2 test users (see below)
python manage.py runserver
```

API runs at `http://localhost:8000/api/`.

**Seeded credentials:** See [Demo Accounts](#demo-accounts) above.

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

### Authentication (public)

| Method | Endpoint | Description | Success | Key Errors |
|--------|----------|-------------|---------|------------|
| `POST` | `/api/auth/register/` | Create account, return token | `201` | `400` validation, `409` username taken |
| `POST` | `/api/auth/login/` | Authenticate, return token | `200` | `400` missing fields, `401` bad credentials |

Response shape for both: `{ "token": "...", "user_id": 1, "username": "..." }`

### Features (authenticated)

All endpoints below require the `Authorization: Token <key>` header. Unauthenticated → `401`.

| Method | Endpoint | Description | Success | Key Errors | Permission |
|--------|----------|-------------|---------|------------|------------|
| `GET` | `/api/features/` | List features, ranked by pinned → votes → recency | `200` | — | Any user |
| `GET` | `/api/features/?search=term` | Search by title/description | `200` | — | Any user |
| `POST` | `/api/features/` | Create a feature request | `201` | `400` validation, `429` rate limit | Any user |
| `PATCH` | `/api/features/{id}/` | Update feature status | `200` | `403` non-staff | Staff only |
| `DELETE` | `/api/features/{id}/` | Delete a feature and its votes | `204` | `403` not owner/staff | Staff or owner |
| `POST` | `/api/features/{id}/vote/` | Upvote a feature | `201` | `403` self-vote, `409` duplicate, `429` rate limit | Any user |
| `DELETE` | `/api/features/{id}/vote/` | Remove your upvote | `200` | `404` not voted | Any user |
| `DELETE` | `/api/features/{id}/vote/{vote_id}/` | Remove any vote (moderation) | `200` | `403` non-staff | Staff only |
| `PATCH` | `/api/features/{id}/pin/` | Toggle pinned status | `200` | `403` non-staff | Staff only |

## Data Model

```
User (Django built-in auth.User)
  id              Integer (PK, auto)
  username        CharField, unique
  password        Hashed
  is_staff        Boolean                          ← admin flag

FeatureRequest
  id              UUID (PK)
  title           CharField(200)
  description     TextField
  author          FK → User
  status          CharField(20), choices, indexed   ← under_review | planned | in_progress | shipped
  is_pinned       BooleanField, indexed             ← staff-controlled, always sorted first
  vote_count      PositiveIntegerField, indexed     ← denormalized for O(1) ranking
  created_at      DateTimeField
  updated_at      DateTimeField
  ── CHECK vote_count >= 0

Vote
  id              UUID (PK)
  user            FK → User
  feature_request FK → FeatureRequest
  created_at      DateTimeField
  ── UNIQUE (user, feature_request)
```

## Tests

```bash
cd backend
python manage.py test features.tests -v2
```

41 tests across 7 classes:

| Class | Tests | What it proves |
|-------|-------|----------------|
| `VoteIntegrityTests` | 3 | Duplicate vote → 409, self-vote → 403, unvote without vote → 404 |
| `VoteCountTests` | 3 | Vote increments to 1, unvote decrements to 0, two voters yield count of 2 (all via `refresh_from_db`) |
| `AuthAndSerializerTests` | 8 | Unauthenticated → 401, register + login flow, duplicate register → 409, bad password → 401, spoofed author ignored, injected vote_count ignored, feature create throttled after 5, vote throttled after 30 |
| `RankingTests` | 6 | Vote count descending order, recency tiebreaker, search by title, search by description, search preserves ranking, empty search returns all |
| `AdminPermissionTests` | 11 | Staff can update status / non-staff 403, staff can delete any feature / owner can delete own / non-staff 403, staff can delete any vote / non-staff 403, staff can pin / non-staff 403, pinned appears first, response includes is_pinned and is_staff |
| `AuthAndPermissionTests` | 9 | Unauthenticated → 401, non-staff cannot PATCH status → 403, staff can PATCH status → 200, non-staff cannot delete other's feature → 403, owner can delete own → 204, staff can delete any → 204, non-staff cannot pin → 403, staff can toggle pin → 200, pinned beats high vote count in ranking |
| `RaceConditionTests` | 1 | Two threads via `threading.Barrier` — exactly one 201 + one 409, one Vote row, `vote_count` = 1. Skipped on SQLite; runs on Postgres. |

## Technical Decisions

| Decision | What and why |
|----------|-------------|
| **Token auth over session auth** | Stateless — no server-side session storage, no CSRF token management. The token is stored in localStorage and sent as a header. Simple to implement, simple to test, works naturally with SPAs and CORS. |
| **`is_staff` as admin flag** | Django's built-in `is_staff` boolean is sufficient for a two-tier permission model (regular vs admin). A custom Role model or django-guardian adds complexity with no proportional benefit for this scope. |
| **Denormalized `vote_count`** | Avoids `COUNT(*)` JOIN on every list query. Updated atomically inside `transaction.atomic()` using `F("vote_count") + 1`. The `CheckConstraint` prevents it from going negative. |
| **`UniqueConstraint` on Vote** | One-vote-per-user-per-feature enforced at the database level. If a race condition hits the application check, the constraint catches it and the view returns `409`. |
| **Pinned-first ordering** | `ORDER BY -is_pinned, -vote_count, -created_at` — a product decision that lets admins surface important announcements or urgent requests above the popularity ranking. The `db_index` on `is_pinned` keeps the sort efficient. |
| **Optimistic updates with rollback** | All mutations (vote, unvote, status change, pin toggle, delete) update the UI instantly via TanStack Query cache manipulation, then reconcile with the server. On error, the previous state is restored. Users never wait for the network. |
| **Separate read/write serializers** | `FeatureRequestListSerializer` includes viewer-specific computed fields (`has_voted`, `is_own`, `is_staff`). `FeatureRequestCreateSerializer` accepts only `title` and `description` — the `author` is set from `request.user` server-side, not from client input. `FeatureStatusUpdateSerializer` exposes only `status` for the staff PATCH endpoint. |
| **Batch `has_voted` resolution** | The list view fetches the user's voted feature IDs in a single query, then passes the set into serializer context. This avoids N+1 queries — one DB hit instead of one per card. |
| **Explicit `order_by` in the view** | Ranking is `ORDER BY -is_pinned, -vote_count, -created_at`, stated at the call site rather than buried in `Meta.ordering`. The indexed columns let Postgres satisfy this without a filesort. |
| **No signals for vote count** | Vote count updates happen inline in the vote/unvote view, wrapped in `transaction.atomic()`. Signals fail silently, run outside the request's transaction, and obscure the data flow. Inline updates are explicit and testable. |
| **Rate limiting keyed on user.pk** | DRF's `SimpleRateThrottle` with `get_cache_key` overridden to use the authenticated user's primary key. 5 creates/hour, 30 votes/hour. Uses LocMemCache in dev — comment notes Redis is needed for multi-process production. |
| **PWA over native mobile** | A service worker and web manifest get us home-screen installability. The Tailwind layout is mobile-first. This ships in minutes and covers the "accessible on mobile" requirement without a second codebase. |
| **No pagination** | With fewer than 1,000 expected items for a demo, pagination adds routing and state complexity with no user-facing benefit. Listed as a next step. |

## Project Structure

```
├── backend/
│   ├── config/                  # Django settings, root URL config
│   │   ├── settings.py          # DATABASE_URL, CORS, DRF + TokenAuth config
│   │   └── urls.py
│   ├── features/                # Single Django app — all domain logic
│   │   ├── models.py            # FeatureRequest, Vote (FK to auth.User)
│   │   ├── views.py             # list/create, detail/delete, vote, pin
│   │   ├── auth_views.py        # register + login endpoints
│   │   ├── serializers.py       # list, create, status-update serializers
│   │   ├── throttles.py         # FeatureCreateThrottle, VoteThrottle
│   │   ├── exceptions.py        # Custom 429 response formatting
│   │   ├── urls.py              # All API routes
│   │   ├── tests.py             # 41 tests across 7 classes
│   │   ├── admin.py             # Django admin with inline status editing
│   │   └── management/commands/
│   │       └── seed_demo.py     # 8 features + demo/admin users
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # AuthPage, Header, SubmitForm, FeatureList, FeatureCard, VoteButton, EmptyState
│   │   ├── hooks/               # useFeatures, useVote, useAdmin
│   │   ├── lib/                 # api.ts, auth.ts, schemas.ts
│   │   ├── App.tsx              # Token gate + QueryClientProvider
│   │   └── main.tsx             # Entry point, service worker registration
│   ├── public/                  # manifest.json, sw.js, favicon.svg
│   ├── package.json
│   ├── vercel.json              # SPA routing config
│   └── vite.config.ts           # Tailwind plugin, /api proxy to Django
├── Dockerfile                   # python:3.11-slim + gunicorn
├── docker-compose.yml           # Backend container (no DB — Supabase is external)
├── .github/workflows/ci.yml     # Django tests on push/PR
├── DEPLOYMENT.md                # Vercel + Railway + Supabase deployment guide
└── README.md
```

## What I'd Build Next (4–8 hours)

- **OAuth social login** — GitHub and Google via `django-allauth`, letting users sign in without creating a password
- **Email verification** — require email confirmation on registration before allowing votes
- **Audit log for admin actions** — record who changed status, pinned, or deleted what and when, viewable by staff
- **Redis for distributed rate limiting** — swap LocMemCache for `django-redis` so throttle state is shared across gunicorn workers
- **Cursor pagination** — keyset pagination on `(is_pinned, vote_count, created_at)` for infinite scroll without offset drift
- **WebSocket vote updates** — Django Channels to push vote count changes to all connected clients in real time
- **Dark mode** — Tailwind's `dark:` variant with system preference detection and manual toggle
- **Full-text search** — Postgres `tsvector` index on title and description for ranked relevance instead of `icontains`
