# Requirements Traceability

This matrix starts in Phase 1 and must be completed as implementation and tests land.

| Requirement | Implementation | Verification | Status |
| --- | --- | --- | --- |
| REQ-F-01 Registered auth | `apps/web/src/lib/supabase.ts`, `apps/web/src/lib/auth.tsx`, `apps/web/src/pages/Login.tsx`, `Register.tsx` | Manual/browser testing pending | Partial |
| REQ-F-02 Dashboard/history | `apps/web/src/pages/Dashboard.tsx`, `GET /api/v1/documents` | Live Supabase core smoke test passed; E2E pending | Partial |
| REQ-F-03 PDF upload | `apps/web/src/pages/Upload.tsx`, `apps/api/app/api/v1/router.py` | Pending integration tests | Partial |
| REQ-F-04 Pipeline progress | `apps/api/app/models/state.py` | `apps/api/tests/test_state.py` | Partial |
| REQ-F-05 Summary | `apps/api/app/schemas/content.py`, `LearningPackage.tsx`, DeepSeek provider | Unit tests plus live DeepSeek/Supabase smoke test | Partial |
| REQ-F-06 Flashcards | `apps/api/app/schemas/content.py`, DeepSeek provider, `apps/web/src/pages/LearningPackage.tsx` | Live DeepSeek/Supabase smoke test generated 10 cards; component tests pending | Partial |
| REQ-F-07 Quiz | `apps/api/app/schemas/content.py`, DeepSeek provider, quiz attempt endpoints, `LearningPackage.tsx` | Unit scoring tests and live Supabase core smoke test passed | Partial |
| REQ-F-08 Video | `apps/worker/worker/scene_sanitizer.py`, `video_assets` video plan fields | Scene sanitizer tests plus live DeepSeek video-plan persistence | Partial |
| REQ-F-09 Persistent history | `supabase/migrations/202609030001_initial_schema.sql` | Pending RLS tests | Partial |
| REQ-F-10 Guest upload | `POST /guest/session`, `Upload.tsx`, `guest_sessions` table | Live Supabase smoke test passed | Partial |
| REQ-F-11 Quotas | `apps/api/app/services/quota.py`, `public.accept_upload_event` RPC | Unit tests and live guest 429 smoke test passed | Partial |
| REQ-F-12 Invalid PDFs | `apps/api/app/services/pdf_validation.py`, `apps/api/app/services/pdf_extraction.py` | Unit tests for malformed/tiny/page-limit paths; more fixtures pending | Partial |
| REQ-F-13 Retry | `POST /api/v1/documents/{id}/retry`, source PDF storage | Live Supabase storage/retry smoke test passed; worker retry pending | Partial |
| REQ-F-14 Delete package | `DELETE /api/v1/documents/{id}`, storage cleanup, cascade-backed document deletion, dashboard delete action | Live Supabase core and storage smoke tests passed | Partial |
| REQ-F-15 Signed URLs | `GET /api/v1/video-assets/{id}/playback-url`, `GET /api/v1/video-assets/{id}/download-url` | Live Supabase signed-URL smoke test passed with stored MP4 path; real render pending | Partial |
| REQ-F-16 TTS fallback | `apps/worker/worker/tts.py` | Pending worker tests | Partial |
| REQ-F-17 Refresh-safe jobs | `processing_jobs` migration | Pending integration tests | Partial |
| REQ-F-18 Prompt injection defense | `docs/security-threat-model.md`, `apps/api/app/services/deepseek_generation.py` | Prompt tests pending | Partial |
| REQ-F-19 OpenAPI | FastAPI app config | Pending contract tests | Partial |
| REQ-F-20 Accessibility | CSS focus/reduced motion, route semantics | Pending axe/component tests | Partial |
| REQ-F-21 Observability | Health endpoints | Pending structured logs/metrics | Partial |
| REQ-F-22 Deployment docs | `docs/deployment-railway.md` | Manual review | Partial |
| REQ-F-23 Traceability | This file | Ongoing review | Partial |
| BR-01 Registered users 5/day | Config and quota helper | Pending atomic DB function | Partial |
| BR-02 Guests 1/day | Config, quota helper, `accept_upload_event` RPC | Live guest limit smoke test passed | Partial |
| REQ-NF-01 Security | Threat model, RLS policies, private bucket, server-only service role | Supabase advisors checked; pre-existing non-SmartLearn warning remains | Partial |
| REQ-NF-02 Performance targets | `docs/validation-plan.md` | Pending benchmarks | Partial |
| REQ-NF-03 Reliability | State machine and jobs table | Pending worker tests | Partial |
| REQ-NF-04 Usability | Web shell | Pending SUS study | Partial |
| REQ-NF-05 Accessibility | Web CSS and semantics | Pending automated/manual checks | Partial |
| REQ-NF-06 Maintainability | Monorepo scaffold | Lint/tests pending | Partial |
| REQ-NF-07 Scalability | Worker separation | Pending load test | Partial |
| REQ-NF-08 Privacy | Retention docs | Pending cleanup implementation | Partial |
| REQ-NF-09 Compliance-ready logging | Error envelope | Pending structured log policy | Partial |
| REQ-NF-10 Availability | Health checks | Pending deploy validation | Partial |
| REQ-NF-11 Portability | Env-based config | Pending Railway deploy | Partial |
| REQ-NF-12 Testability | Mock providers/tests | Pending full suite | Partial |
| REQ-NF-13 Documentation | `docs/*`, `README.md` | Manual review | Partial |
