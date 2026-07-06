-- Rollback 20260705_003: drop items and sources tables
DELETE FROM app.traderie_migrations WHERE version = 20260705_003;
DROP TABLE IF EXISTS app.sources CASCADE;
DROP TABLE IF EXISTS app.items CASCADE;
