# Architecture

```mermaid
flowchart LR
  Web[React Web App] --> API[FastAPI REST API]
  API --> Auth[Supabase Auth]
  API --> DB[(Supabase Postgres)]
  API --> Storage[Private Supabase Storage]
  Worker[Railway Worker] --> DB
  Worker --> DeepSeek[DeepSeek API]
  Worker --> TTS[TTS Provider]
  Worker --> Manim[Safe Manim Renderer]
  Worker --> Storage
```

```mermaid
stateDiagram-v2
  [*] --> uploaded
  uploaded --> validating
  validating --> extracting
  extracting --> generating_content
  generating_content --> content_ready
  content_ready --> generating_audio
  generating_audio --> rendering_video
  rendering_video --> completed
  generating_audio --> partial_success
  rendering_video --> partial_success
  validating --> failed
  extracting --> failed
  generating_content --> failed
  rendering_video --> failed
  completed --> deleted
  partial_success --> deleted
  failed --> deleted
```

The API accepts uploads, validates files before quota consumption, creates durable database jobs, and returns status immediately. The worker leases jobs from Postgres, persists content before video rendering, and uploads private media objects. Clients poll status and request short-lived signed URLs only after backend authorization.
