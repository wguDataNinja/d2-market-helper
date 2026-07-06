-- Rollback 20260705_004: drop snapshot_runs table
DELETE FROM app.traderie_migrations WHERE version = 20260705_004;
DROP TABLE IF EXISTS app.snapshot_runs CASCADE;
