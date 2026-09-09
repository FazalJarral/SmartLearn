# Data Model

The database model is normalized in `supabase/migrations/202609030001_initial_schema.sql` and is applied to Supabase project `fbdxelbvltgvypygprmn`.

Core ownership:

- `profiles` maps registered users to `auth.users`.
- `guest_sessions` stores hashed anonymous session secrets and expiry metadata.
- `documents` belongs to exactly one registered user or guest session.
- `learning_packages`, `flashcards`, `quiz_questions`, `video_assets`, and jobs cascade from documents/packages.
- `quiz_attempts` belongs to exactly one registered user or guest session.
- `usage_events` records accepted and rejected upload decisions with idempotency keys.
- `accept_upload_event` atomically records accepted/rejected upload events under an actor-level advisory lock.

RLS:

- Every table has RLS enabled.
- Registered access policies start with profile/document ownership.
- Guest content is intentionally accessed through backend service-role endpoints rather than anonymous table policies.
- Private storage bucket `smartlearn-private` is configured for PDF, MP4, and transcript assets. Playback/download should be served through backend-issued signed URLs.
- `learning_packages.definitions` stores the complete plain-language glossary, while `learning_packages.topics` stores the topic inventory and safe follow-up search suggestions.
- `video_assets` stores the validated safe Manim scene DSL plan (`plan_title`, `narration`, `scenes`) separately from rendered media paths. AI output is data only; the application maps it to trusted Manim animations.

Retention:

- Registered learning packages persist until user deletion.
- Guest sessions expire after the configured TTL. Cleanup must delete guest documents, package records, and private storage objects.
- Source PDFs default to a short retention window. Raw extracted text should not be stored indefinitely unless a later phase documents a bounded operational need.
