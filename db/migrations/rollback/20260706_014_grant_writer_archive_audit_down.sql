-- Rollback 20260706_014: remove writer archive audit grant.

SET ROLE traderie_owner;

REVOKE SELECT, INSERT ON archive.prune_archive_audit FROM traderie_writer;

DELETE FROM app.traderie_migrations WHERE version = 14;

RESET ROLE;
