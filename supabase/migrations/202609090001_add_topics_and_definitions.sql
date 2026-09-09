alter table public.learning_packages
add column if not exists definitions jsonb not null default '[]'::jsonb,
add column if not exists topics jsonb not null default '[]'::jsonb;

comment on column public.learning_packages.definitions is
  'Plain-language definitions for terms and named concepts in the source document.';
comment on column public.learning_packages.topics is
  'Document topic inventory with safe follow-up learning search suggestions.';
