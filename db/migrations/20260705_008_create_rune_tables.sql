SET ROLE traderie_owner;

-- 20260705_008_create_rune_tables.sql
-- Rune price registry, per-segment rune values, and ruleset breakdowns.

CREATE TABLE IF NOT EXISTS app.rune_registry (
    rune_id         integer PRIMARY KEY,
    name            text NOT NULL,
    short_name      text NOT NULL,
    tier            text NOT NULL CHECK (tier IN ('low', 'medium', 'high')),
    in_game_key     text,
    tools_key       text,
    cash_key        text,
    cash_slug       text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.segment_rune_prices (
    rune_price_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id        uuid NOT NULL REFERENCES app.product_builds(build_id) ON DELETE CASCADE,
    segment_slug    text NOT NULL REFERENCES app.segments(segment_slug),
    rune_id         integer NOT NULL REFERENCES app.rune_registry(rune_id),
    rune_name       text NOT NULL,
    value_ist       numeric(10,4),
    bid_price       numeric(10,4),
    ask_price       numeric(10,4),
    bid_count       integer NOT NULL DEFAULT 0,
    ask_count       integer NOT NULL DEFAULT 0,
    total_trades    integer NOT NULL DEFAULT 0,
    confidence      text NOT NULL DEFAULT 'unavailable' CHECK (confidence IN ('high', 'medium', 'low', 'unavailable')),
    confidence_reason text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_segment_rune_prices_build ON app.segment_rune_prices(build_id);
CREATE INDEX IF NOT EXISTS idx_segment_rune_prices_segment ON app.segment_rune_prices(segment_slug);

CREATE TABLE IF NOT EXISTS app.ruleset_breakdowns (
    breakdown_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id            uuid NOT NULL REFERENCES app.product_builds(build_id) ON DELETE CASCADE,
    segment_slug        text NOT NULL REFERENCES app.segments(segment_slug),
    ruleset             text NOT NULL CHECK (ruleset IN ('rotw', 'lod', 'classic', 'mixed', 'unknown')),
    count               integer NOT NULL DEFAULT 0,
    pct                 numeric(5,2) NOT NULL DEFAULT 0,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ruleset_breakdowns_build ON app.ruleset_breakdowns(build_id);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (8, '20260705_008_create_rune_tables', 'placeholder-checksum', 0);

RESET ROLE;
