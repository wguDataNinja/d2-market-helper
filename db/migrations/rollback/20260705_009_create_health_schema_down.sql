-- Rollback 20260705_009: drop health schema tables
DELETE FROM app.traderie_migrations WHERE version = 20260705_009;
DROP TABLE IF EXISTS health.workflow_status CASCADE;
DROP TABLE IF EXISTS health.health_runs CASCADE;
