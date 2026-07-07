-- Validate writer can use archive schema.

SELECT 'writer_archive_schema_usage' AS check_name,
       CASE WHEN has_schema_privilege('traderie_writer', 'archive', 'USAGE')
       THEN 'PASS' ELSE 'FAIL' END AS result;
