# Deployment

The practical free/demo deployment split is:

- Frontend: Cloudflare Pages.
- API: Render free web service or Railway container service.
- Worker: deploy later as a separate paid/trial worker service once Manim/TTS rendering is enabled.

Cloudflare Workers can host static assets and lightweight Python APIs, but the current SmartLearn API uses FastAPI multipart uploads plus PyMuPDF. Keep the API on a Python container host unless the API is deliberately adapted and revalidated for Cloudflare Python Workers.

## Cloudflare Pages Frontend

Build from the repository root:

```bash
$env:VITE_API_BASE_URL="https://your-api-host.example.com/api/v1"
npm run build:web
npx wrangler pages deploy apps/web/dist --project-name smartlearn --branch main
```

The current Cloudflare Pages project is `smartlearn`.

After the API is deployed, rebuild and redeploy the frontend with `VITE_API_BASE_URL` pointing to that API. The initial direct upload can render the UI, but upload/authenticated API actions require a reachable backend URL.

## Render API

`render.yaml` defines a free Docker-backed web service named `smartlearn-api`.

Required secret/runtime values:

- `API_CORS_ORIGINS`: include the Cloudflare Pages URL.
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DEEPSEEK_API_KEY`

The Dockerfile listens on the provider `PORT` and exposes:

- `/health/live`
- `/health/ready`

Render free web services are suitable for demos and testing, but can sleep after inactivity and have usage limits.

## Railway API

Deploy as a Docker service from the repository root using `apps/api/Dockerfile`.

Build command:

```bash
pip install -e apps/api
```

Start command:

```bash
uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port $PORT
```

Health checks:

- `/health/live`
- `/health/ready`

## Worker

Build command:

```bash
pip install -e apps/worker
```

Start command:

```bash
python -m worker.runner
```

The worker image requires FFmpeg, Manim Community Edition, and LaTeX packages before real rendering is enabled. Temporary render output should use ephemeral disk and upload final MP4/transcripts to private Supabase storage.

## Frontend

Deploy `apps/web` with:

```bash
npm install
npm run build:web
```

Serve `apps/web/dist` over HTTPS. Configure `VITE_API_BASE_URL` to the production API `/api/v1` base.
