-- Rollback 20260705_001: drop schemas and migration table
DROP TABLE IF EXISTS app.traderie_migrations CASCADE;
DROP SCHEMA IF EXISTS archive CASCADE;
DROP SCHEMA IF EXISTS health CASCADE;
DROP SCHEMA IF EXISTS app CASCADE;
