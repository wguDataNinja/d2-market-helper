SET ROLE traderie_owner;

-- 20260705_005_create_completed_trades.sql
-- Core trade observation table. One row per deduped observation.
-- See CODEX_SESSION_1_ARCHITECTURE.md §12.

CREATE TABLE IF NOT EXISTS app.completed_trades (
    trade_observation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug         text NOT NULL REFERENCES app.segments(segment_slug),
    observation_key      text NOT NULL,
    listing_id           integer NOT NULL,
    content_hash         text NOT NULL,
    item_id              integer NOT NULL,
    item_name            text NOT NULL,
    quantity             integer NOT NULL DEFAULT 1,
    seller               text,
    seller_rating        numeric(3,1),
    seller_reviews       integer,
    seller_score         integer,
    seller_status        text,
    updated_at           timestamptz,
    captured_at          timestamptz NOT NULL,
    active               boolean,
    completed            boolean DEFAULT true,
    platform             text,
    mode                 text CHECK (mode IN ('softcore', 'hardcore')),
    hardcore             boolean NOT NULL DEFAULT false,
    ladder               boolean,
    game_version         text,
    ruleset              text NOT NULL DEFAULT 'unknown' CHECK (ruleset IN ('rotw', 'lod', 'classic', 'mixed', 'unknown')),
    has_and_prices       boolean NOT NULL DEFAULT false,
    price_group_count    integer NOT NULL DEFAULT 1,
    price_entry_count    integer NOT NULL DEFAULT 1,
    source_payload       jsonb DEFAULT '{}'::jsonb,
    snapshot_run_id      uuid REFERENCES app.snapshot_runs(snapshot_run_id),
    ingested_at          timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_completed_trades_obs_key ON app.completed_trades(segment_slug, observation_key);
CREATE INDEX IF NOT EXISTS idx_completed_trades_listing ON app.completed_trades(segment_slug, listing_id);
CREATE INDEX IF NOT EXISTS idx_completed_trades_captured ON app.completed_trades(segment_slug, captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_completed_trades_content_hash ON app.completed_trades(content_hash);
CREATE INDEX IF NOT EXISTS idx_completed_trades_ruleset ON app.completed_trades(ruleset);
CREATE INDEX IF NOT EXISTS idx_completed_trades_item ON app.completed_trades(item_id);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (5, '20260705_005_create_completed_trades', 'placeholder-checksum', 0);

RESET ROLE;
