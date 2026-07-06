-- Rollback 20260705_006: drop price_entries table
DELETE FROM app.traderie_migrations WHERE version = 20260705_006;
DROP TABLE IF EXISTS app.price_entries CASCADE;
