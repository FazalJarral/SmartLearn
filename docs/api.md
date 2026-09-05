# API Notes

OpenAPI is served by the API at `/api/v1/openapi.json` and interactive docs at `/api/v1/docs`.

Local Supabase-backed mode uses:

- `SUPABASE_URL=https://fbdxelbvltgvypygprmn.supabase.co`
- Browser auth through `@supabase/supabase-js`
- Backend service-role access for guest sessions, quota RPCs, and controlled guest-owned object access
- Backend-only DeepSeek generation when `GENERATION_PROVIDER=deepseek`

Implemented core endpoint surface:

- `POST /api/v1/guest/session`
- `GET /api/v1/me/usage`
- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{id}`
- `DELETE /api/v1/documents/{id}`
- `GET /api/v1/documents/{id}/status`
- `GET /api/v1/learning-packages/{id}`
- `POST /api/v1/learning-packages/{id}/quiz-attempts`
- `PATCH /api/v1/quiz-attempts/{id}/answers`
- `POST /api/v1/quiz-attempts/{id}/complete`
- `POST /api/v1/documents/{id}/retry`
- `GET /api/v1/video-assets/{id}/playback-url`
- `GET /api/v1/video-assets/{id}/download-url`
- `GET /health/live`
- `GET /health/ready`

Remaining required endpoint surface:

- Worker-owned Manim/TTS execution must still write rendered media paths before playback/download URLs return successfully for real packages.

Error responses use a stable envelope:

```json
{
  "error": {
    "code": "invalid_pdf_signature",
    "message": "The file does not appear to be a valid PDF.",
    "request_id": "uuid",
    "fields": {}
  }
}
```

Object ownership is inferred from the authenticated Supabase JWT or controlled guest session. Ownership is never accepted from request bodies.
