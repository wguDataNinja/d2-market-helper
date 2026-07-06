SET ROLE traderie_owner;

-- 20260705_006_create_price_entries.sql
-- Normalized price entries extracted from completed_trades price array.
-- Enables querying of AND trades, group/add flags, and non-Ist pairs.

CREATE TABLE IF NOT EXISTS app.price_entries (
    price_entry_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id            uuid NOT NULL REFERENCES app.completed_trades(trade_observation_id) ON DELETE CASCADE,
    requested_item_id   integer,
    item_name           text NOT NULL,
    quantity            integer NOT NULL DEFAULT 1,
    add_flag            boolean DEFAULT false,
    group_number        integer DEFAULT 0,
    rune_item_id        integer,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_price_entries_trade ON app.price_entries(trade_id);
CREATE INDEX IF NOT EXISTS idx_price_entries_item ON app.price_entries(requested_item_id);
CREATE INDEX IF NOT EXISTS idx_price_entries_rune ON app.price_entries(rune_item_id);
CREATE INDEX IF NOT EXISTS idx_price_entries_add ON app.price_entries(trade_id, add_flag);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (6, '20260705_006_create_price_entries', 'placeholder-checksum', 0);

RESET ROLE;
