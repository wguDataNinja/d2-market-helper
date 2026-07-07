SET ROLE traderie_owner;

-- 20260706_010_create_collection_run_metrics.sql
-- One row per collection run, with collector diagnostics and segment rollups.

CREATE TABLE IF NOT EXISTS app.collection_run_metrics (
    run_id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_run_id           uuid REFERENCES app.snapshot_runs(snapshot_run_id) ON DELETE SET NULL,
    workflow                  text NOT NULL DEFAULT 'traderie_collection',
    source_id                 text REFERENCES app.sources(source_id) ON DELETE SET NULL,
    source_slug               text REFERENCES app.sources(source_id) ON DELETE SET NULL,
    segment_slug              text REFERENCES app.segments(segment_slug) ON DELETE SET NULL,
    trigger_type              text NOT NULL DEFAULT 'manual' CHECK (trigger_type IN ('scheduled', 'manual', 'backfill', 'retry', 'pilot')),
    started_at                timestamptz NOT NULL,
    completed_at              timestamptz,
    elapsed_ms                integer CHECK (elapsed_ms IS NULL OR elapsed_ms >= 0),
    requests_made             integer NOT NULL DEFAULT 0 CHECK (requests_made >= 0),
    response_bytes            bigint NOT NULL DEFAULT 0 CHECK (response_bytes >= 0),
    records_returned          integer NOT NULL DEFAULT 0 CHECK (records_returned >= 0),
    records_new               integer NOT NULL DEFAULT 0 CHECK (records_new >= 0),
    records_skipped_duplicate integer NOT NULL DEFAULT 0 CHECK (records_skipped_duplicate >= 0),
    duplicate_ratio           numeric(8,6) CHECK (duplicate_ratio IS NULL OR (duplicate_ratio >= 0 AND duplicate_ratio <= 1)),
    retries                   integer NOT NULL DEFAULT 0 CHECK (retries >= 0),
    failures                  integer NOT NULL DEFAULT 0 CHECK (failures >= 0),
    stop_reason               text,
    collector_version         text,
    error_summary             jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_diagnostics        jsonb NOT NULL DEFAULT '{}'::jsonb,
    segment_breakdown         jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_collection_run_metrics_started
    ON app.collection_run_metrics(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_run_metrics_workflow_trigger
    ON app.collection_run_metrics(workflow, trigger_type, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_run_metrics_source_segment
    ON app.collection_run_metrics(source_id, segment_slug, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_run_metrics_source_slug_segment
    ON app.collection_run_metrics(source_slug, segment_slug, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_collection_run_metrics_snapshot
    ON app.collection_run_metrics(snapshot_run_id)
    WHERE snapshot_run_id IS NOT NULL;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (10, '20260706_010_create_collection_run_metrics', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
