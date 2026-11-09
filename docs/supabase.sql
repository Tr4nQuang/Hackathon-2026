-- Run once in the Supabase SQL Editor. See section 7.1 of docs/PLAN.md.
create table plays (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  run_id uuid not null unique,
  session_id uuid not null,
  mode text not null check (mode in ('tutorial','level','endless')),
  scenario_id text not null,
  level_id text not null,
  attempt_number int not null default 1 check (attempt_number >= 1),
  package_index int,
  chosen_rules jsonb,
  player_rules text check (char_length(player_rules) <= 1000),
  rules_used int,
  rules_chars int,
  grade text,
  stars int check (stars between 0 and 3),
  score int check (score between 0 and 100),
  security_pct int check (security_pct between 0 and 100),
  helpfulness_pct int check (helpfulness_pct between 0 and 100),
  core_hacked boolean,
  leaked_zones jsonb,
  refused_zones jsonb,
  guide_skipped boolean,
  ai_model text,
  ai_temperature numeric,
  engine_version text,
  words int,
  word_budget int,
  blocks_used int,
  attacks_blocked int,
  customers_blocked int,
  vip_lost boolean,
  trust_after int,
  live_ai boolean,
  visits jsonb,
  constraint mode_fields check (
    (mode = 'endless' and player_rules is not null and chosen_rules is null)
    or (mode in ('tutorial','level') and chosen_rules is not null)
  )
);

alter table plays enable row level security;
create policy "anon can insert plays" on plays
  for insert to anon with check (true);

-- Needed because 'Automatically expose new tables' is switched off in the project settings.
grant insert on table public.plays to anon;

-- No select policy on purpose: the public key can insert but never read.

-- Upgrade an existing table to engine_version 3.0.0 (live shifts). Safe to run more than once.
-- Level rows now keep the rules text too; visits holds one record per visitor (chat texts only with live AI).
alter table plays add column if not exists words int;
alter table plays add column if not exists word_budget int;
alter table plays add column if not exists blocks_used int;
alter table plays add column if not exists attacks_blocked int;
alter table plays add column if not exists customers_blocked int;
alter table plays add column if not exists vip_lost boolean;
alter table plays add column if not exists trust_after int;
alter table plays add column if not exists live_ai boolean;
alter table plays add column if not exists visits jsonb;
alter table plays drop constraint if exists mode_fields;
alter table plays add constraint mode_fields check (
  (mode = 'endless' and player_rules is not null and chosen_rules is null)
  or (mode in ('tutorial','level') and chosen_rules is not null)
);
