-- Rollback 20260706_012: drop prune/archive audit tables
SET ROLE traderie_owner;

DELETE FROM app.traderie_migrations WHERE version = 12;
DROP TABLE IF EXISTS archive.prune_archive_audit CASCADE;
DROP TABLE IF EXISTS app.prune_audit CASCADE;

RESET ROLE;
