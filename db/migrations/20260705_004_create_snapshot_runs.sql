SET ROLE traderie_owner;

-- 20260705_004_create_snapshot_runs.sql
-- Tracks each snapshot collection run per segment.

CREATE TABLE IF NOT EXISTS app.snapshot_runs (
    snapshot_run_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug        text NOT NULL REFERENCES app.segments(segment_slug),
    run_timestamp       timestamptz NOT NULL,
    status              text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'partial')),
    item_count          integer,
    listing_count       integer,
    error_count         integer,
    duration_seconds    integer,
    metadata            jsonb DEFAULT '{}'::jsonb,
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (segment_slug, run_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_snapshot_runs_segment ON app.snapshot_runs(segment_slug);
CREATE INDEX IF NOT EXISTS idx_snapshot_runs_timestamp ON app.snapshot_runs(run_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_snapshot_runs_status ON app.snapshot_runs(status);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (4, '20260705_004_create_snapshot_runs', 'placeholder-checksum', 0);

RESET ROLE;
