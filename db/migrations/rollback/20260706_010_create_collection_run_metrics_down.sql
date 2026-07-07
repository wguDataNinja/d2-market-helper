-- Rollback 20260706_010: drop collection_run_metrics table
SET ROLE traderie_owner;

DELETE FROM app.traderie_migrations WHERE version = 10;
DROP TABLE IF EXISTS app.collection_run_metrics CASCADE;

RESET ROLE;
