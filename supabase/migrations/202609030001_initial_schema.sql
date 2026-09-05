-- SmartLearn v1.0 normalized schema.

create extension if not exists "pgcrypto";

create schema if not exists private;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'smartlearn-private',
  'smartlearn-private',
  false,
  15728640,
  array['application/pdf', 'video/mp4', 'text/plain']
)
on conflict (id) do update
set public = excluded.public,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create type document_status as enum (
  'uploaded',
  'validating',
  'extracting',
  'generating_content',
  'content_ready',
  'generating_audio',
  'rendering_video',
  'completed',
  'partial_success',
  'failed',
  'deleted'
);

create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public, private
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1)))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function private.handle_new_user();

create table guest_sessions (
  id uuid primary key default gen_random_uuid(),
  token_hash text not null unique,
  expires_at timestamptz not null,
  abuse_fingerprint_hash text,
  accepted_uploads_today integer not null default 0,
  created_at timestamptz not null default now()
);

create table documents (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid references profiles(id) on delete cascade,
  guest_session_id uuid references guest_sessions(id) on delete cascade,
  original_filename text not null,
  source_storage_path text,
  size_bytes integer not null check (size_bytes > 0),
  page_count integer check (page_count between 1 and 20),
  checksum_sha256 text not null,
  status document_status not null default 'uploaded',
  created_at timestamptz not null default now(),
  deleted_at timestamptz,
  check ((owner_user_id is not null) <> (guest_session_id is not null))
);

create table processing_jobs (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents(id) on delete cascade,
  stage document_status not null,
  progress integer not null default 0 check (progress between 0 and 100),
  attempts integer not null default 0,
  max_attempts integer not null default 3,
  lease_owner text,
  leased_until timestamptz,
  heartbeat_at timestamptz,
  error_code text,
  user_message text,
  diagnostic_detail text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (document_id, stage)
);

create table learning_packages (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null unique references documents(id) on delete cascade,
  title text not null,
  overview text not null,
  key_points jsonb not null,
  schema_version text not null default '1.0',
  model_version text,
  prompt_version text,
  completed_at timestamptz,
  created_at timestamptz not null default now()
);

create table flashcards (
  id uuid primary key default gen_random_uuid(),
  package_id uuid not null references learning_packages(id) on delete cascade,
  position integer not null,
  front text not null,
  back text not null,
  source_pages jsonb not null default '[]'::jsonb,
  unique (package_id, position)
);

create table quiz_questions (
  id uuid primary key default gen_random_uuid(),
  package_id uuid not null references learning_packages(id) on delete cascade,
  position integer not null,
  question text not null,
  options jsonb not null,
  correct_index integer not null check (correct_index between 0 and 3),
  explanation text not null,
  source_pages jsonb not null default '[]'::jsonb,
  unique (package_id, position)
);

create table quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  package_id uuid not null references learning_packages(id) on delete cascade,
  owner_user_id uuid references profiles(id) on delete cascade,
  guest_session_id uuid references guest_sessions(id) on delete cascade,
  score integer not null default 0,
  total integer not null default 0,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  check ((owner_user_id is not null) <> (guest_session_id is not null))
);

create table quiz_answers (
  id uuid primary key default gen_random_uuid(),
  attempt_id uuid not null references quiz_attempts(id) on delete cascade,
  question_id uuid not null references quiz_questions(id) on delete cascade,
  selected_index integer not null check (selected_index between 0 and 3),
  is_correct boolean not null,
  answered_at timestamptz not null default now(),
  unique (attempt_id, question_id)
);

create table video_assets (
  id uuid primary key default gen_random_uuid(),
  package_id uuid not null unique references learning_packages(id) on delete cascade,
  status document_status not null default 'content_ready',
  video_storage_path text,
  transcript_storage_path text,
  duration_seconds integer,
  narration_available boolean not null default false,
  error_code text,
  user_message text,
  diagnostic_detail text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table usage_events (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid references profiles(id) on delete cascade,
  guest_session_id uuid references guest_sessions(id) on delete cascade,
  accepted boolean not null,
  reason text,
  idempotency_key text not null,
  occurred_at timestamptz not null default now(),
  check ((owner_user_id is not null) <> (guest_session_id is not null))
);

create unique index usage_events_actor_idempotency_idx
  on usage_events (owner_user_id, idempotency_key)
  where owner_user_id is not null;

create unique index usage_events_guest_idempotency_idx
  on usage_events (guest_session_id, idempotency_key)
  where guest_session_id is not null;

create index documents_owner_idx on documents(owner_user_id, created_at desc);
create index documents_guest_idx on documents(guest_session_id, created_at desc);
create index processing_jobs_lease_idx on processing_jobs(stage, leased_until);
create index usage_events_utc_day_idx on usage_events((occurred_at at time zone 'utc'::text), accepted);
create index usage_events_owner_day_idx on usage_events(owner_user_id, occurred_at desc) where accepted;
create index usage_events_guest_day_idx on usage_events(guest_session_id, occurred_at desc) where accepted;

alter table profiles enable row level security;
alter table guest_sessions enable row level security;
alter table documents enable row level security;
alter table processing_jobs enable row level security;
alter table learning_packages enable row level security;
alter table flashcards enable row level security;
alter table quiz_questions enable row level security;
alter table quiz_attempts enable row level security;
alter table quiz_answers enable row level security;
alter table video_assets enable row level security;
alter table usage_events enable row level security;

create policy "profiles-own-read" on profiles for select using (auth.uid() = id);
create policy "profiles-own-update" on profiles for update using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

create policy "documents-own-read" on documents for select to authenticated using ((select auth.uid()) = owner_user_id);
create policy "jobs-own-read" on processing_jobs for select to authenticated using (
  exists (
    select 1 from documents
    where documents.id = processing_jobs.document_id
      and documents.owner_user_id = (select auth.uid())
  )
);
create policy "packages-own-read" on learning_packages for select to authenticated using (
  exists (
    select 1 from documents
    where documents.id = learning_packages.document_id
      and documents.owner_user_id = (select auth.uid())
  )
);
create policy "flashcards-own-read" on flashcards for select to authenticated using (
  exists (
    select 1
    from learning_packages lp
    join documents d on d.id = lp.document_id
    where lp.id = flashcards.package_id
      and d.owner_user_id = (select auth.uid())
  )
);
create policy "quiz-questions-own-read" on quiz_questions for select to authenticated using (
  exists (
    select 1
    from learning_packages lp
    join documents d on d.id = lp.document_id
    where lp.id = quiz_questions.package_id
      and d.owner_user_id = (select auth.uid())
  )
);
create policy "quiz-attempts-own-read" on quiz_attempts for select to authenticated using ((select auth.uid()) = owner_user_id);
create policy "quiz-answers-own-read" on quiz_answers for select to authenticated using (
  exists (
    select 1 from quiz_attempts qa
    where qa.id = quiz_answers.attempt_id
      and qa.owner_user_id = (select auth.uid())
  )
);
create policy "video-assets-own-read" on video_assets for select to authenticated using (
  exists (
    select 1
    from learning_packages lp
    join documents d on d.id = lp.document_id
    where lp.id = video_assets.package_id
      and d.owner_user_id = (select auth.uid())
  )
);
create policy "usage-events-own-read" on usage_events for select to authenticated using ((select auth.uid()) = owner_user_id);

create policy "smartlearn-storage-own-read" on storage.objects for select to authenticated using (
  bucket_id = 'smartlearn-private'
  and (storage.foldername(name))[1] = 'users'
  and (storage.foldername(name))[2] = (select auth.uid())::text
);

create policy "smartlearn-storage-own-insert" on storage.objects for insert to authenticated with check (
  bucket_id = 'smartlearn-private'
  and (storage.foldername(name))[1] = 'users'
  and (storage.foldername(name))[2] = (select auth.uid())::text
);

create or replace function public.accept_upload_event(
  actor_user_id uuid,
  actor_guest_session_id uuid,
  upload_idempotency_key text,
  daily_limit integer,
  event_reason text default null
)
returns table (
  accepted boolean,
  accepted_today integer,
  daily_limit_out integer,
  remaining integer,
  resets_at_utc timestamptz,
  reused boolean
)
language plpgsql
security invoker
as $$
declare
  day_start timestamptz := date_trunc('day', now() at time zone 'utc') at time zone 'utc';
  day_end timestamptz := day_start + interval '1 day';
  existing public.usage_events%rowtype;
begin
  if (actor_user_id is null) = (actor_guest_session_id is null) then
    raise exception 'exactly one actor is required';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(coalesce(actor_user_id::text, actor_guest_session_id::text), 0));

  select * into existing
  from public.usage_events
  where idempotency_key = upload_idempotency_key
    and (
      (actor_user_id is not null and owner_user_id = actor_user_id)
      or (actor_guest_session_id is not null and guest_session_id = actor_guest_session_id)
    )
  limit 1;

  if found then
    select count(*) into accepted_today
    from public.usage_events
    where accepted
      and occurred_at >= day_start
      and occurred_at < day_end
      and (
        (actor_user_id is not null and owner_user_id = actor_user_id)
        or (actor_guest_session_id is not null and guest_session_id = actor_guest_session_id)
      );
    accepted := existing.accepted;
    daily_limit_out := daily_limit;
    remaining := greatest(daily_limit - accepted_today, 0);
    resets_at_utc := day_end;
    reused := true;
    return next;
    return;
  end if;

  select count(*) into accepted_today
  from public.usage_events
  where accepted
    and occurred_at >= day_start
    and occurred_at < day_end
    and (
      (actor_user_id is not null and owner_user_id = actor_user_id)
      or (actor_guest_session_id is not null and guest_session_id = actor_guest_session_id)
    );

  accepted := accepted_today < daily_limit;
  if accepted then
    accepted_today := accepted_today + 1;
  end if;

  insert into public.usage_events (
    owner_user_id,
    guest_session_id,
    accepted,
    reason,
    idempotency_key
  )
  values (
    actor_user_id,
    actor_guest_session_id,
    accepted,
    coalesce(event_reason, case when accepted then 'accepted' else 'quota_exceeded' end),
    upload_idempotency_key
  );

  daily_limit_out := daily_limit;
  remaining := greatest(daily_limit - accepted_today, 0);
  resets_at_utc := day_end;
  reused := false;
  return next;
end;
$$;

create or replace function public.cleanup_expired_guest_sessions(batch_size integer default 100)
returns integer
language plpgsql
security invoker
as $$
declare
  deleted_count integer;
begin
  delete from public.guest_sessions
  where id in (
    select id
    from public.guest_sessions
    where expires_at < now()
    limit batch_size
  );
  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$;

revoke all on function private.handle_new_user() from public;
revoke all on function public.accept_upload_event(uuid, uuid, text, integer, text) from public;
revoke all on function public.cleanup_expired_guest_sessions(integer) from public;

grant usage on schema public to anon, authenticated, service_role;
grant usage on schema private to service_role;

grant select, update on public.profiles to authenticated;
grant select on public.documents, public.processing_jobs, public.learning_packages, public.flashcards, public.quiz_questions, public.quiz_attempts, public.quiz_answers, public.video_assets, public.usage_events to authenticated;
grant all on all tables in schema public to service_role;
grant execute on function public.accept_upload_event(uuid, uuid, text, integer, text) to service_role;
grant execute on function public.cleanup_expired_guest_sessions(integer) to service_role;

-- Guest rows are intentionally not exposed through broad anonymous RLS policies.
-- Backend and worker use the service role for controlled guest access, deletion, and signed URLs.
