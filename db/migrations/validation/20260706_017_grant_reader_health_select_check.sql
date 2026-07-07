-- Validate reader can read health schema for sanitized health export.

SELECT 'reader_health_select' AS check_name,
       CASE WHEN
         has_schema_privilege('traderie_reader', 'health', 'USAGE')
         AND has_table_privilege('traderie_reader', 'health.health_runs', 'SELECT')
         AND has_table_privilege('traderie_reader', 'health.workflow_status', 'SELECT')
       THEN 'PASS' ELSE 'FAIL' END AS result;
