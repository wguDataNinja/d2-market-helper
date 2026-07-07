-- Rollback 20260706_017: remove reader health select.

SET ROLE traderie_owner;

REVOKE SELECT ON ALL TABLES IN SCHEMA health FROM traderie_reader;
REVOKE USAGE ON SCHEMA health FROM traderie_reader;

DELETE FROM app.traderie_migrations WHERE version = 17;

RESET ROLE;
