SET ROLE traderie_owner;

-- 20260705_009_create_health_schema.sql
-- Private health monitoring tables.
-- See CODEX_SESSION_1_ARCHITECTURE.md §8.

CREATE TABLE IF NOT EXISTS health.health_runs (
    run_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow            text NOT NULL,
    status              text NOT NULL CHECK (status IN ('ok', 'warn', 'fail', 'skip')),
    started_at          timestamptz NOT NULL,
    finished_at         timestamptz,
    last_success_at     timestamptz,
    expected_cadence    interval,
    freshness_age       interval,
    records_read        integer DEFAULT 0,
    records_written     integer DEFAULT 0,
    records_rejected    integer DEFAULT 0,
    backlog             integer DEFAULT 0,
    retry_count         integer DEFAULT 0,
    error_class         text,
    error_code          text,
    error_message_private text,
    deployed_revision   text,
    schema_version      integer,
    migration_version   integer,
    scheduler_state     text,
    backup_state        text CHECK (backup_state IN ('ok', 'stale', 'fail')),
    storage_bytes       bigint,
    storage_growth_bytes_24h bigint,
    incident_state      text DEFAULT 'none' CHECK (incident_state IN ('none', 'active', 'resolved')),
    metadata            jsonb DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_health_runs_workflow ON health.health_runs(workflow, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_runs_status ON health.health_runs(status);

CREATE TABLE IF NOT EXISTS health.workflow_status (
    workflow_id         text PRIMARY KEY,
    workflow            text NOT NULL UNIQUE,
    status              text NOT NULL CHECK (status IN ('ok', 'warn', 'fail', 'skip')),
    last_run_id         uuid REFERENCES health.health_runs(run_id),
    last_success_at     timestamptz,
    last_failure_at     timestamptz,
    failure_count       integer NOT NULL DEFAULT 0,
    incident_state      text DEFAULT 'none' CHECK (incident_state IN ('none', 'active', 'resolved')),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (9, '20260705_009_create_health_schema', 'placeholder-checksum', 0);

RESET ROLE;
