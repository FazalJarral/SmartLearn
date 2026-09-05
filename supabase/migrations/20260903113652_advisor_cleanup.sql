drop policy if exists "profiles-own-read" on public.profiles;
create policy "profiles-own-read" on public.profiles
for select
to authenticated
using ((select auth.uid()) = id);

create or replace function public.cleanup_expired_guest_sessions(batch_size integer default 100)
returns integer
language plpgsql
security invoker
set search_path = public
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
set search_path = public
as $$
declare
  day_start timestamptz := date_trunc('day', now() at time zone 'utc') at time zone 'utc';
  day_end timestamptz := day_start + interval '1 day';
  existing public.usage_events%rowtype;
  existing_count integer;
  event_accepted boolean;
begin
  if (actor_user_id is null) = (actor_guest_session_id is null) then
    raise exception 'exactly one actor is required';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(coalesce(actor_user_id::text, actor_guest_session_id::text), 0));

  select * into existing
  from public.usage_events ue
  where ue.idempotency_key = upload_idempotency_key
    and (
      (actor_user_id is not null and ue.owner_user_id = actor_user_id)
      or (actor_guest_session_id is not null and ue.guest_session_id = actor_guest_session_id)
    )
  limit 1;

  if found then
    select count(*) into existing_count
    from public.usage_events ue
    where ue.accepted = true
      and ue.occurred_at >= day_start
      and ue.occurred_at < day_end
      and (
        (actor_user_id is not null and ue.owner_user_id = actor_user_id)
        or (actor_guest_session_id is not null and ue.guest_session_id = actor_guest_session_id)
      );
    accepted := existing.accepted;
    accepted_today := existing_count;
    daily_limit_out := daily_limit;
    remaining := greatest(daily_limit - existing_count, 0);
    resets_at_utc := day_end;
    reused := true;
    return next;
    return;
  end if;

  select count(*) into existing_count
  from public.usage_events ue
  where ue.accepted = true
    and ue.occurred_at >= day_start
    and ue.occurred_at < day_end
    and (
      (actor_user_id is not null and ue.owner_user_id = actor_user_id)
      or (actor_guest_session_id is not null and ue.guest_session_id = actor_guest_session_id)
    );

  event_accepted := existing_count < daily_limit;
  if event_accepted then
    existing_count := existing_count + 1;
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
    event_accepted,
    coalesce(event_reason, case when event_accepted then 'accepted' else 'quota_exceeded' end),
    upload_idempotency_key
  );

  accepted := event_accepted;
  accepted_today := existing_count;
  daily_limit_out := daily_limit;
  remaining := greatest(daily_limit - existing_count, 0);
  resets_at_utc := day_end;
  reused := false;
  return next;
end;
$$;

revoke all on function public.accept_upload_event(uuid, uuid, text, integer, text) from public;
revoke all on function public.cleanup_expired_guest_sessions(integer) from public;
grant execute on function public.accept_upload_event(uuid, uuid, text, integer, text) to service_role;
grant execute on function public.cleanup_expired_guest_sessions(integer) to service_role;
