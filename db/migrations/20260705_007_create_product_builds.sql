SET ROLE traderie_owner;

-- 20260705_007_create_product_builds.sql
-- Tracks product regeneration runs and metadata.

CREATE TABLE IF NOT EXISTS app.product_builds (
    build_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug    text NOT NULL REFERENCES app.segments(segment_slug),
    generated_at    timestamptz NOT NULL,
    status          text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    schema_version  text,
    total_trades    integer,
    unique_listings integer,
    product_path    text,
    metadata        jsonb DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_builds_segment ON app.product_builds(segment_slug);
CREATE INDEX IF NOT EXISTS idx_product_builds_generated ON app.product_builds(generated_at DESC);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (7, '20260705_007_create_product_builds', 'placeholder-checksum', 0);

RESET ROLE;
