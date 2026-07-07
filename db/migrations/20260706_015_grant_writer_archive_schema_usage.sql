SET ROLE traderie_owner;

-- 20260706_015_grant_writer_archive_schema_usage.sql
-- Required with table-level archive audit grants.

GRANT USAGE ON SCHEMA archive TO traderie_writer;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (15, '20260706_015_grant_writer_archive_schema_usage', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
