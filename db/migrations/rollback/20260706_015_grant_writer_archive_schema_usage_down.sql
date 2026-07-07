-- Rollback 20260706_015: remove writer usage on archive schema.

SET ROLE traderie_owner;

REVOKE USAGE ON SCHEMA archive FROM traderie_writer;

DELETE FROM app.traderie_migrations WHERE version = 15;

RESET ROLE;
