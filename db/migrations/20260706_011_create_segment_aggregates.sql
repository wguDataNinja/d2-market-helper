SET ROLE traderie_owner;

-- 20260706_011_create_segment_aggregates.sql
-- Hourly/daily rune price aggregates by source and isolated economy segment.

CREATE TABLE IF NOT EXISTS app.segment_aggregates (
    aggregate_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_start          timestamptz NOT NULL,
    bucket_end            timestamptz NOT NULL,
    source_id             text DEFAULT 'traderie' REFERENCES app.sources(source_id) ON DELETE SET NULL,
    source_slug           text DEFAULT 'traderie' REFERENCES app.sources(source_id) ON DELETE SET NULL,
    segment_slug          text NOT NULL REFERENCES app.segments(segment_slug),
    rune_id               integer NOT NULL REFERENCES app.rune_registry(rune_id),
    granularity           text NOT NULL CHECK (granularity IN ('hourly', 'daily')),
    observation_count     integer NOT NULL DEFAULT 0 CHECK (observation_count >= 0),
    trade_count           integer NOT NULL DEFAULT 0 CHECK (trade_count >= 0),
    volume_total          numeric(18,6) NOT NULL DEFAULT 0 CHECK (volume_total >= 0),
    vwap                  numeric(18,6),
    median_price          numeric(18,6),
    min_price             numeric(18,6),
    max_price             numeric(18,6),
    first_seen_at         timestamptz,
    last_seen_at          timestamptz,
    run_id                uuid REFERENCES app.collection_run_metrics(run_id) ON DELETE SET NULL,
    generation_metadata   jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at            timestamptz NOT NULL DEFAULT now(),
    CHECK (bucket_end > bucket_start)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_segment_aggregates_source_segment_rune_bucket
    ON app.segment_aggregates(COALESCE(source_id, ''), segment_slug, rune_id, bucket_start, granularity);
CREATE INDEX IF NOT EXISTS idx_segment_aggregates_segment_rune_bucket
    ON app.segment_aggregates(segment_slug, rune_id, granularity, bucket_start DESC);
CREATE INDEX IF NOT EXISTS idx_segment_aggregates_source_segment_bucket
    ON app.segment_aggregates(source_id, segment_slug, granularity, bucket_start DESC);
CREATE INDEX IF NOT EXISTS idx_segment_aggregates_source_slug_segment_bucket
    ON app.segment_aggregates(source_slug, segment_slug, granularity, bucket_start DESC);
CREATE INDEX IF NOT EXISTS idx_segment_aggregates_run
    ON app.segment_aggregates(run_id)
    WHERE run_id IS NOT NULL;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (11, '20260706_011_create_segment_aggregates', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
