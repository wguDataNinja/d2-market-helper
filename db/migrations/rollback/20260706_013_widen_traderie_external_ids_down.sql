-- Rollback 20260706_013: restore external ID columns to integer.
-- Only safe if all values fit signed 32-bit integer.

SET ROLE traderie_owner;

ALTER TABLE app.price_entries
    ALTER COLUMN requested_item_id TYPE integer,
    ALTER COLUMN rune_item_id TYPE integer;

ALTER TABLE app.completed_trades
    ALTER COLUMN listing_id TYPE integer,
    ALTER COLUMN item_id TYPE integer;

ALTER TABLE app.items
    ALTER COLUMN item_id TYPE integer;

DELETE FROM app.traderie_migrations WHERE version = 13;

RESET ROLE;
