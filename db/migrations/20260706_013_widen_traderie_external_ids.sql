SET ROLE traderie_owner;

-- 20260706_013_widen_traderie_external_ids.sql
-- Traderie listing IDs and external item IDs exceed signed 32-bit integer.

ALTER TABLE app.items
    ALTER COLUMN item_id TYPE bigint;

ALTER TABLE app.completed_trades
    ALTER COLUMN listing_id TYPE bigint,
    ALTER COLUMN item_id TYPE bigint;

ALTER TABLE app.price_entries
    ALTER COLUMN requested_item_id TYPE bigint,
    ALTER COLUMN rune_item_id TYPE bigint;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (13, '20260706_013_widen_traderie_external_ids', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
