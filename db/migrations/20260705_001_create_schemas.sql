SET ROLE traderie_owner;

-- 20260705_001_create_schemas.sql
-- Create database schemas and migration tracking table.
-- Forward-only — schema drops are rollback-only.

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS health;
CREATE SCHEMA IF NOT EXISTS archive;

CREATE TABLE IF NOT EXISTS app.traderie_migrations (
    version     integer PRIMARY KEY,
    name        text NOT NULL,
    checksum_sha256 text NOT NULL,
    applied_at  timestamptz NOT NULL DEFAULT now(),
    applied_by  text NOT NULL DEFAULT current_user,
    duration_ms integer NOT NULL CHECK (duration_ms >= 0)
);

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (1, '20260705_001_create_schemas', 'placeholder-checksum', 0);

RESET ROLE;
