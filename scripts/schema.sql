CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS reviews (
  id TEXT PRIMARY KEY,
  created_at timestamptz,
  user_id text,
  region text,
  rating int,
  text text
);

CREATE TABLE IF NOT EXISTS agent_outputs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text,
  agent_name text,
  record_refs jsonb,
  summary text,
  details jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS merged_insights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text,
  agent_name text,
  merged_summary text,
  details jsonb,
  provenance jsonb,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id text,
  agent_name text,
  fork_name text,
  log text,
  status text,
  started_at timestamptz,
  finished_at timestamptz
);