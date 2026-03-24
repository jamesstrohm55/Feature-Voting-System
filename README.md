# FeatureVote

A full-stack feature voting system built with Django + React. Users can submit feature requests, browse existing ones, and upvote the ideas they care about. Features are ranked by popularity in real time.

## Architecture

```
┌──────────────────┐         ┌──────────────────┐
│  React + Vite    │  HTTP   │  Django + DRF    │
│  (TypeScript)    │ ──────► │  (Python)        │
│  TanStack Query  │  /api/* │  SQLite / Postgres│
│  Tailwind CSS    │         │  (Supabase)      │
└──────────────────┘         └──────────────────┘
```

**Key decisions:**
- **Django is the sole backend** — React calls Django APIs, never Supabase directly
- **Anonymous session identity** — UUID stored in localStorage, sent as `X-Session-Id` header. No login required
- **Denormalized vote counts** — `vote_count` column on `FeatureRequest` for O(1) ranking, updated atomically with `F()` expressions
- **PWA-installable** — responsive mobile-first design with service worker and web manifest

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.1, Django REST Framework |
| Frontend | React 19, TypeScript, Vite |
| Styling | Tailwind CSS 4 |
| Data Fetching | TanStack Query v5 |
| Validation | Zod (client), DRF serializers (server) |
| Database | SQLite (dev) / Supabase Postgres (prod) |
| Mobile | Responsive PWA |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# Configure database (defaults to SQLite)
cp .env.example .env
# Edit .env with your Supabase DATABASE_URL if using Postgres

python manage.py migrate
python manage.py runserver
```

API is now running at `http://localhost:8000/api/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App is now running at `http://localhost:5173/`. Vite proxies `/api/*` to Django.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/features/` | List all features, ranked by votes |
| `POST` | `/api/features/` | Create a new feature request |
| `POST` | `/api/features/{id}/vote/` | Upvote a feature |
| `DELETE` | `/api/features/{id}/vote/` | Remove your upvote |

All requests require the `X-Session-Id` header. The frontend handles this automatically.

## Data Model

- **Voter** — anonymous identity keyed by session ID
- **FeatureRequest** — title, description, author, denormalized vote_count
- **Vote** — junction table with unique constraint (voter, feature_request)

Vote integrity enforced at the Postgres level via `UniqueConstraint`.

## Project Structure

```
├── backend/
│   ├── config/          # Django project settings
│   ├── features/        # Main app: models, views, serializers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React UI components
│   │   ├── hooks/       # TanStack Query hooks
│   │   └── lib/         # API client, session, Zod schemas
│   └── public/          # PWA manifest, service worker
└── README.md
```

## Trade-offs

| Decision | Rationale |
|----------|-----------|
| Anonymous sessions vs real auth | Zero friction for a take-home demo. Production would add OAuth |
| Denormalized `vote_count` | O(1) sorting vs O(n) COUNT join. Atomic updates via `F()` |
| PWA vs native mobile app | Ships instantly, same codebase, installable |
| No pagination | <1000 items expected. Pagination is P1 |
| No signals for vote count | Inline in views with `transaction.atomic()` — explicit and testable |
