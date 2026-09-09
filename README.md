# SmartLearn

SmartLearn is a responsive study app for university learners. A learner uploads a text-based academic PDF and receives a structured summary with plain-language definitions, a topic inventory with further-learning suggestions, flashcards, a self-marking quiz, and an animated Manim explainer.

The project is production-oriented: the API validates uploads, enforces quotas, stores private files in Supabase Storage, generates study material with DeepSeek when configured, persists normalized learning data, and hands queued video assets to a background worker.

## Architecture

- `apps/web`: React, TypeScript, Vite, Tailwind, React Router, TanStack Query.
- `apps/api`: FastAPI API with versioned REST endpoints, upload validation, auth boundaries, quotas, and job orchestration.
- `apps/worker`: database-backed background worker for queued video artifacts.
- `supabase/migrations`: normalized Postgres schema and RLS policies.
- `docs`: architecture, data model, security, deployment, validation, and traceability.

## Local Prerequisites

- Node.js 22+
- Python 3.12 for target deployment. Python 3.13 is acceptable for local scaffold tests until pinned dependencies require 3.12.
- Supabase project for real auth/storage/database, or mock mode for local tests.
- Manim Community and its Cairo/Pango dependencies for animated video rendering (included in the Docker images).

## Setup

```powershell
npm install
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -e apps/api[dev]
pip install -e apps/worker[dev]
Copy-Item .env.example .env
```

## Run

```powershell
npm run dev:web
uvicorn app.main:app --app-dir apps/api --reload
python -m worker.runner
```

## Test

```powershell
npm run build:web
npm run test:web
python -m pytest apps/api/tests
python -m pytest apps/worker/tests
```

Normal automated tests use mock DeepSeek, mock storage, and dummy TTS. Paid external providers are excluded from default test runs.

For real study-material generation, set these only in server-side env:

```env
GENERATION_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-key
DEEPSEEK_MODEL=deepseek-v4-flash
```

For production, also set:

```env
ENVIRONMENT=production
API_CORS_ORIGINS=https://your-frontend-origin.example
SUPABASE_URL=your-project-url
SUPABASE_ANON_KEY=your-anon-or-publishable-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_STORAGE_BUCKET=smartlearn-private
```

## Deployment

`render.yaml` defines two Docker services on Render:

- `smartlearn-api`: FastAPI web service with `/health/ready` readiness checks.
- `smartlearn-worker`: long-running worker that processes queued video assets.

The frontend can deploy to a static host such as Vercel, Netlify, Cloudflare Pages, Render static sites, or Sites. Configure `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY` for that frontend environment.
