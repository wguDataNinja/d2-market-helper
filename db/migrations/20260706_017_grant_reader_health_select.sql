SET ROLE traderie_owner;

-- 20260706_017_grant_reader_health_select.sql
-- Sanitized health export reads health runs plus app retention summaries.

GRANT USAGE ON SCHEMA health TO traderie_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA health TO traderie_reader;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (17, '20260706_017_grant_reader_health_select', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
