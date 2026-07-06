SET ROLE traderie_owner;

-- 20260705_003_create_items_and_sources.sql
-- Items tracked by Traderie and data sources.

CREATE TABLE IF NOT EXISTS app.items (
    item_id         integer PRIMARY KEY,
    name            text NOT NULL,
    category        text NOT NULL DEFAULT 'rune' CHECK (category IN ('rune', 'gem', 'misc')),
    short_name      text,
    tier            text CHECK (tier IN ('low', 'medium', 'high')),
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS app.sources (
    source_id       text PRIMARY KEY,
    name            text NOT NULL,
    source_type     text NOT NULL CHECK (source_type IN ('api', 'parser', 'browser', 'manual')),
    category        text NOT NULL DEFAULT 'completed_player_trades' CHECK (category IN ('completed_player_trades', 'cash_market', 'forum_reference', 'community_discussion')),
    priority        text CHECK (priority IN ('tier_1', 'tier_2', 'tier_3', 'later')),
    status          text NOT NULL DEFAULT 'discovered' CHECK (status IN ('integrated', 'parser_prototype_ready', 'captured_browser', 'captured_static', 'discovered', 'deferred')),
    base_url        text,
    enabled         boolean NOT NULL DEFAULT false,
    metadata        jsonb DEFAULT '{}'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sources_status ON app.sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_type ON app.sources(source_type);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (3, '20260705_003_create_items_and_sources', 'placeholder-checksum', 0);

RESET ROLE;
