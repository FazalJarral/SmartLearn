# SmartLearn

SmartLearn is a responsive study app for university learners. A learner uploads a text-based academic PDF and receives a structured summary, flashcards, a self-marking quiz, and an asynchronously rendered instructional video.

This repository is currently in Phase 1: a runnable monorepo scaffold with mock provider seams, state-machine contracts, normalized database migrations, and documentation placeholders that map the SRS into implementation work.

## Architecture

- `apps/web`: React, TypeScript, Vite, Tailwind, React Router, TanStack Query.
- `apps/api`: FastAPI API with versioned REST endpoints, upload validation, auth boundaries, quotas, and job orchestration.
- `apps/worker`: database-backed background worker for generation, TTS, and Manim rendering.
- `supabase/migrations`: normalized Postgres schema and RLS policies.
- `docs`: architecture, data model, security, deployment, validation, and traceability.

## Local Prerequisites

- Node.js 22+
- Python 3.12 for target deployment. Python 3.13 is acceptable for local scaffold tests until pinned dependencies require 3.12.
- Supabase project for real auth/storage/database, or mock mode for local tests.
- Manim/FFmpeg/LaTeX for real video rendering.

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

## Deployment

The API and worker target Railway as separate services. The frontend can deploy to a static host such as Vercel, Netlify, Cloudflare Pages, or Railway static serving. See `docs/deployment-railway.md`.
