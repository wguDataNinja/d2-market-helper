-- Validate writer can insert/read archive prune audit rows.

SELECT 'writer_archive_audit_select_insert' AS check_name,
       CASE WHEN
         has_table_privilege('traderie_writer', 'archive.prune_archive_audit', 'SELECT')
         AND has_table_privilege('traderie_writer', 'archive.prune_archive_audit', 'INSERT')
       THEN 'PASS' ELSE 'FAIL' END AS result;
