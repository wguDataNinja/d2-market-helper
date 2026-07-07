-- Rollback 20260706_011: drop segment_aggregates table
SET ROLE traderie_owner;

DELETE FROM app.traderie_migrations WHERE version = 11;
DROP TABLE IF EXISTS app.segment_aggregates CASCADE;

RESET ROLE;
