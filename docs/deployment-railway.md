# Railway Deployment

Deploy separate Railway services for the API and worker.

## API

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
