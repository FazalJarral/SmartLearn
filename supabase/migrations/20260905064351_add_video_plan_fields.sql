alter table public.video_assets
add column if not exists plan_title text,
add column if not exists narration text,
add column if not exists scenes jsonb not null default '[]'::jsonb;

comment on column public.video_assets.plan_title is 'Validated document-grounded video plan title from the generation schema.';
comment on column public.video_assets.narration is 'Validated narration text used for transcript/TTS.';
comment on column public.video_assets.scenes is 'Validated safe scene DSL entries; never executable code.';
