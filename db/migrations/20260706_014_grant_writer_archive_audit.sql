SET ROLE traderie_owner;

-- 20260706_014_grant_writer_archive_audit.sql
-- Prune apply archives rows before deletion; writer needs bounded insert/read.

GRANT SELECT, INSERT ON archive.prune_archive_audit TO traderie_writer;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (14, '20260706_014_grant_writer_archive_audit', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
