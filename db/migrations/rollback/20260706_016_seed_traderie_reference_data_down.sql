-- Rollback 20260706_016 reference seed rows.
-- Safe only before dependent aggregate/product rows exist.

SET ROLE traderie_owner;

DELETE FROM app.rune_registry WHERE rune_id BETWEEN 1 AND 33;
DELETE FROM app.sources WHERE source_id = 'traderie';
DELETE FROM app.traderie_migrations WHERE version = 16;

RESET ROLE;
