-- 999_full_validation.sql
-- Traderie full structural, ownership, grant, and isolation validation.

\set ON_ERROR_STOP on

SELECT 'row_count_app.segments' AS check_name, COUNT(*) AS row_count FROM app.segments
UNION ALL SELECT 'row_count_app.items', COUNT(*) FROM app.items
UNION ALL SELECT 'row_count_app.sources', COUNT(*) FROM app.sources
UNION ALL SELECT 'row_count_app.completed_trades', COUNT(*) FROM app.completed_trades
UNION ALL SELECT 'row_count_app.price_entries', COUNT(*) FROM app.price_entries
UNION ALL SELECT 'row_count_app.collection_run_metrics', COUNT(*) FROM app.collection_run_metrics
UNION ALL SELECT 'row_count_app.segment_aggregates', COUNT(*) FROM app.segment_aggregates
UNION ALL SELECT 'row_count_app.prune_audit', COUNT(*) FROM app.prune_audit
UNION ALL SELECT 'row_count_archive.prune_archive_audit', COUNT(*) FROM archive.prune_archive_audit
UNION ALL SELECT 'row_count_health.health_runs', COUNT(*) FROM health.health_runs
UNION ALL SELECT 'row_count_health.workflow_status', COUNT(*) FROM health.workflow_status;

WITH expected(schema_name) AS (
    VALUES ('app'), ('archive'), ('health')
)
SELECT 'schemas_exist' AS check_name,
       CASE WHEN COUNT(n.nspname) = 3 THEN 'PASS' ELSE 'FAIL' END AS result,
       ARRAY_AGG(n.nspname ORDER BY n.nspname) AS found
FROM expected e
LEFT JOIN pg_namespace n ON n.nspname = e.schema_name;

WITH expected(table_schema, table_name) AS (
    VALUES
        ('app','traderie_migrations'),
        ('app','segments'),
        ('app','items'),
        ('app','sources'),
        ('app','snapshot_runs'),
        ('app','completed_trades'),
        ('app','price_entries'),
        ('app','product_builds'),
        ('app','rune_registry'),
        ('app','segment_rune_prices'),
        ('app','ruleset_breakdowns'),
        ('app','collection_run_metrics'),
        ('app','segment_aggregates'),
        ('app','prune_audit'),
        ('archive','prune_archive_audit'),
        ('health','health_runs'),
        ('health','workflow_status')
)
SELECT 'expected_tables_exist' AS check_name,
       CASE WHEN COUNT(c.oid) = 17 THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(c.oid) AS found
FROM expected e
LEFT JOIN pg_namespace n ON n.nspname = e.table_schema
LEFT JOIN pg_class c ON c.relnamespace = n.oid
               AND c.relname = e.table_name
               AND c.relkind = 'r';

SELECT 'schema_ownership' AS check_name,
       CASE WHEN COUNT(*) = 3 THEN 'PASS' ELSE 'FAIL' END AS result
FROM pg_namespace n
JOIN pg_roles r ON r.oid = n.nspowner
WHERE n.nspname IN ('app','archive','health')
  AND r.rolname = 'traderie_owner';

SELECT 'table_ownership' AS check_name,
       CASE WHEN COUNT(*) = 17 THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(*) AS owned_tables
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_roles r ON r.oid = c.relowner
WHERE n.nspname IN ('app','archive','health')
  AND c.relkind = 'r'
  AND r.rolname = 'traderie_owner';

SELECT 'migration_versions' AS check_name,
       CASE WHEN COUNT(*) IN (0, 17) THEN 'PASS' ELSE 'FAIL' END AS result,
       ARRAY_AGG(version ORDER BY version) AS versions
FROM app.traderie_migrations
WHERE version BETWEEN 1 AND 17;

SELECT 'segments_reference_rows' AS check_name,
       CASE WHEN COUNT(*) IN (0, 4) THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(*) AS segment_count
FROM app.segments;

SELECT 'primary_keys' AS check_name,
       CASE WHEN COUNT(*) >= 17 THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(*) AS pk_count
FROM information_schema.table_constraints
WHERE table_schema IN ('app','archive','health')
  AND constraint_type = 'PRIMARY KEY';

SELECT 'foreign_keys' AS check_name,
       CASE WHEN COUNT(*) >= 21 THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(*) AS fk_count
FROM information_schema.table_constraints
WHERE table_schema IN ('app','archive','health')
  AND constraint_type = 'FOREIGN KEY';

SELECT 'writer_app_dml' AS check_name,
       CASE WHEN NOT EXISTS (
           SELECT 1
           FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'app'
             AND c.relkind = 'r'
             AND NOT (
                 has_table_privilege('traderie_writer', c.oid, 'SELECT')
                 AND has_table_privilege('traderie_writer', c.oid, 'INSERT')
                 AND has_table_privilege('traderie_writer', c.oid, 'UPDATE')
                 AND has_table_privilege('traderie_writer', c.oid, 'DELETE')
             )
    ) THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'writer_archive_audit_select_insert' AS check_name,
       CASE WHEN
           has_schema_privilege('traderie_writer', 'archive', 'USAGE')
           AND
           has_table_privilege('traderie_writer', 'archive.prune_archive_audit', 'SELECT')
           AND has_table_privilege('traderie_writer', 'archive.prune_archive_audit', 'INSERT')
       THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'reader_app_select' AS check_name,
       CASE WHEN NOT EXISTS (
           SELECT 1
           FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname = 'app'
             AND c.relkind = 'r'
             AND NOT has_table_privilege('traderie_reader', c.oid, 'SELECT')
       ) THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'reader_health_select' AS check_name,
       CASE WHEN
           has_schema_privilege('traderie_reader', 'health', 'USAGE')
           AND has_table_privilege('traderie_reader', 'health.health_runs', 'SELECT')
           AND has_table_privilege('traderie_reader', 'health.workflow_status', 'SELECT')
       THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'monitor_health_only' AS check_name,
       CASE WHEN has_schema_privilege('traderie_monitor', 'health', 'USAGE')
             AND NOT has_schema_privilege('traderie_monitor', 'app', 'USAGE')
            THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'backup_all_project_tables' AS check_name,
       CASE WHEN NOT EXISTS (
           SELECT 1
           FROM pg_class c
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE n.nspname IN ('app','archive','health')
             AND c.relkind = 'r'
             AND NOT has_table_privilege('traderie_backup', c.oid, 'SELECT')
       ) THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'public_schema_privileges_revoked' AS check_name,
       CASE WHEN NOT EXISTS (
           SELECT 1
           FROM pg_namespace n
           CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) acl
           WHERE n.nspname IN ('app','archive','health')
             AND acl.grantee = 0
             AND acl.privilege_type IN ('USAGE','CREATE')
       ) THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'cross_db_connect_isolation' AS check_name,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(*) AS unexpected_connects
FROM pg_roles r
CROSS JOIN pg_database d
WHERE r.rolname IN ('traderie_writer','traderie_reader','traderie_monitor',
                    'traderie_migrator','traderie_backup')
  AND d.datname IN ('sjc_intel','wgu_reddit_ops','wgu_catalog','bsda_courses',
                    'idlehacking_kb','ih_market_companion','reckless_ben')
  AND has_database_privilege(r.rolname, d.datname, 'CONNECT');

DO $$
DECLARE
    failures text[] := ARRAY[]::text[];
BEGIN
    IF (SELECT COUNT(*) FROM pg_namespace n JOIN pg_roles r ON r.oid = n.nspowner
        WHERE n.nspname IN ('app','archive','health') AND r.rolname = 'traderie_owner') <> 3 THEN
        failures := array_append(failures, 'schema_ownership');
    END IF;

    IF (SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace JOIN pg_roles r ON r.oid = c.relowner
        WHERE n.nspname IN ('app','archive','health') AND c.relkind = 'r' AND r.rolname = 'traderie_owner') <> 17 THEN
        failures := array_append(failures, 'table_ownership');
    END IF;

    IF (SELECT COUNT(*) FROM app.traderie_migrations WHERE version BETWEEN 1 AND 17) NOT IN (0, 17) THEN
        failures := array_append(failures, 'migration_versions');
    END IF;

    IF NOT (
        has_schema_privilege('traderie_writer', 'archive', 'USAGE')
        AND has_table_privilege('traderie_writer', 'archive.prune_archive_audit', 'SELECT')
        AND has_table_privilege('traderie_writer', 'archive.prune_archive_audit', 'INSERT')
    ) THEN
        failures := array_append(failures, 'writer_archive_audit_select_insert');
    END IF;

    IF (SELECT COUNT(*) FROM app.segments) NOT IN (0, 4) THEN
        failures := array_append(failures, 'segments_reference_rows');
    END IF;

    IF (SELECT COUNT(*) FROM information_schema.table_constraints
        WHERE table_schema IN ('app','archive','health') AND constraint_type = 'PRIMARY KEY') < 17 THEN
        failures := array_append(failures, 'primary_keys');
    END IF;

    IF (SELECT COUNT(*) FROM information_schema.table_constraints
        WHERE table_schema IN ('app','archive','health') AND constraint_type = 'FOREIGN KEY') < 21 THEN
        failures := array_append(failures, 'foreign_keys');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'app' AND c.relkind = 'r'
          AND NOT (
              has_table_privilege('traderie_writer', c.oid, 'SELECT')
              AND has_table_privilege('traderie_writer', c.oid, 'INSERT')
              AND has_table_privilege('traderie_writer', c.oid, 'UPDATE')
              AND has_table_privilege('traderie_writer', c.oid, 'DELETE')
          )
    ) THEN
        failures := array_append(failures, 'writer_app_dml');
    END IF;

    IF NOT (
        has_schema_privilege('traderie_reader', 'health', 'USAGE')
        AND has_table_privilege('traderie_reader', 'health.health_runs', 'SELECT')
        AND has_table_privilege('traderie_reader', 'health.workflow_status', 'SELECT')
    ) THEN
        failures := array_append(failures, 'reader_health_select');
    END IF;

    IF NOT (has_schema_privilege('traderie_monitor', 'health', 'USAGE')
            AND NOT has_schema_privilege('traderie_monitor', 'app', 'USAGE')) THEN
        failures := array_append(failures, 'monitor_health_only');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_roles r
        CROSS JOIN pg_database d
        WHERE r.rolname IN ('traderie_writer','traderie_reader','traderie_monitor',
                            'traderie_migrator','traderie_backup')
          AND d.datname IN ('sjc_intel','wgu_reddit_ops','wgu_catalog','bsda_courses',
                            'idlehacking_kb','ih_market_companion','reckless_ben')
          AND has_database_privilege(r.rolname, d.datname, 'CONNECT')
    ) THEN
        failures := array_append(failures, 'cross_db_connect_isolation');
    END IF;

    IF array_length(failures, 1) IS NOT NULL THEN
        RAISE EXCEPTION 'Traderie full validation failed: %', array_to_string(failures, ', ');
    END IF;
END $$;
