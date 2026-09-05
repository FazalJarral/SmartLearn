# SmartLearn Implementation Plan

## Discovery

- Workspace: `F:\Projects\SmartLearn`
- Repository state: empty directory, not a Git repository.
- Existing implementation: none found.
- `.openai/hosting.json`: absent.
- Local tooling observed on 2026-09-03: Node 22.14.0, npm 11.2.0, Python 3.13.2, Git 2.48.1.

## Assumptions

- Because the workspace is empty, Phase 1 is a greenfield scaffold rather than a retrofit.
- Python 3.12 remains the production target even though only Python 3.13 is currently installed locally.
- Provider integrations start in mock/dummy mode. Real DeepSeek, Supabase, TTS, and Manim execution are configured through environment variables in later phases.
- Guest access is brokered only through backend endpoints. Browser clients never receive service-role credentials.

## Phase 1 Scope

- Create monorepo structure for web, API, worker, Supabase, and docs.
- Define versioned schemas and state-machine constants.
- Add health endpoints, mock upload/status routes, and basic UI shell.
- Add normalized migration starter with RLS policy intent.
- Add baseline tests for schemas, quota math, state transitions, and scene sanitization.
- Document remaining gaps honestly in the traceability matrix.

## Phase 1 Checks

Completed on 2026-09-03:

- `npm install`: passed. Reported 7 audit findings in transitive frontend dependencies.
- `pip install -e apps/api[dev]`: passed on local Python 3.13.2 with user-script PATH warnings.
- `pip install -e apps/worker[dev]`: passed on local Python 3.13.2 with user-script PATH warnings.
- `npm run lint:web`: passed.
- `npm run build:web`: passed.
- `npm run test:web`: passed, 1 test.
- `python -m ruff check apps/api apps/worker`: passed after import formatting fix.
- `python -m pytest apps/api/tests apps/worker/tests`: passed, 8 tests.
- `npm audit --audit-level=moderate`: failed with 7 findings. Available fixes require breaking upgrades to Vite 8 and React Router 7, so this is recorded as a dependency-hardening task rather than force-applied in Phase 1.

Not run in Phase 1:

- Supabase migration validation, because no Supabase CLI/project link exists yet.
- End-to-end tests, because the real API persistence/auth pipeline is not implemented yet.
- Manim render validation, because the worker is still in dummy provider mode.

## Next Phases

- Phase 2: real Supabase JWT verification, guest session persistence, atomic quota function, PDF validation/extraction, upload job creation, dashboard/history.
- Phase 3: DeepSeek integration, chunking, strict JSON validation, content persistence, quiz attempts, retries.
- Phase 4: worker leases, TTS adapter, Manim safe scene renderer, storage signed URLs, partial success.
- Phase 5: accessibility, E2E/load tests, observability, deployment hardening, traceability completion.

## Supabase Integration Notes

Completed on 2026-09-03:

- Linked the local repo to Supabase project `SmartLearn` / `fbdxelbvltgvypygprmn`.
- Applied `202609030001_initial_schema.sql` to the remote project.
- Applied `20260903113335_fix_accept_upload_event.sql` to replace the quota RPC after a PL/pgSQL name collision was found by smoke testing.
- Applied `20260903113652_advisor_cleanup.sql` to set stable RPC search paths and optimize the profile RLS policy.
- Verified the remote project has the 11 core SmartLearn tables, private bucket `smartlearn-private`, migration history, and service-role RPCs.
- Populated ignored local env files `.env` and `apps/web/.env.local` with the real project URL and keys. These values are intentionally not copied into tracked docs.
- Wired React to Supabase Auth through `@supabase/supabase-js`.
- Wired the API to verify Supabase bearer sessions, create hashed guest sessions, call the atomic quota RPC, and persist mock study-package records to Supabase.
- Added PyMuPDF text extraction before quota consumption and wired `GENERATION_PROVIDER=deepseek` to a DeepSeek JSON-mode provider.
- Verified `.env` has `GENERATION_PROVIDER=deepseek` and a non-placeholder DeepSeek key without printing the key.
- Added core document history, package deletion, persisted quiz attempts, answer scoring, and quiz completion endpoints.
- Added core frontend flows for recent package history, deletion, flashcard flipping/navigation, scored quiz attempts, and video-plan review.
- Added private source-PDF storage, retry from retained source PDF, storage cleanup on deletion, and authorized signed playback/download URL endpoints.

Smoke test result:

- `POST /api/v1/guest/session`: passed and created a guest row in Supabase.
- `POST /api/v1/documents` with an explicit PDF MIME type: passed and persisted 1 document, 1 learning package, 8 flashcards, 5 quiz questions, and 1 video asset.
- A second accepted upload attempt for the same guest session returned `429 upload_quota_exceeded`, confirming the guest daily limit path.
- `supabase migration list --linked` shows local and remote migration history aligned for `202609030001`, `20260903113335`, and `20260903113652`.
- `supabase db advisors --linked --level warn` no longer reports SmartLearn-created warnings. It still reports a pre-existing `public.rls_auto_enable()` security-definer warning.

Known caveats:

- Upload now performs PyMuPDF parseability, page count, encryption, scanned/image-only rejection, and text extraction before quota consumption.
- DeepSeek generation is implemented and live-tested. An earlier key returned `402 Insufficient Balance`; SmartLearn maps that to `deepseek_insufficient_balance` and records failed document/job state.
- A funded-key smoke test on 2026-09-05 passed end to end through the live API, DeepSeek, and Supabase. It generated/persisted a real package titled `Cellular Respiration: Glucose to ATP` with 8 key points, 10 flashcards, 5 quiz questions, and a 7-scene video plan.
- A core-functionality smoke test on 2026-09-05 passed against the live Supabase project without calling DeepSeek. It verified guest document listing, package read with quiz IDs, quiz attempt creation, answer scoring, quiz completion, and document deletion/cascade cleanup.
- A storage/retry/signed-URL smoke test on 2026-09-05 passed against the live Supabase project with `GENERATION_PROVIDER=mock`. It verified source PDF upload, retry from storage, unavailable-video handling, MP4-path signed playback URL creation, signed download URL creation, and cleanup.
- Temporary smoke rows created before failure-state handling were corrected to `failed`.
- Added `20260905064351_add_video_plan_fields.sql` so DeepSeek video plans are persisted on `video_assets` instead of reconstructed from mock defaults.
- Source PDF storage is enabled for retry and deletion cleanup. A bounded retention cleanup job for expired guest sessions remains pending.
- The advisor still reports a pre-existing Supabase project warning for `public.rls_auto_enable()`, which was not created by SmartLearn.
- A temporary local `tmp-smoke.pdf` fixture may remain because local command policy blocked deletion. It is ignored by `.gitignore`.
