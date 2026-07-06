-- Rollback 20260705_002: drop segments table
DELETE FROM app.traderie_migrations WHERE version = 20260705_002;
DROP TABLE IF EXISTS app.segments CASCADE;
