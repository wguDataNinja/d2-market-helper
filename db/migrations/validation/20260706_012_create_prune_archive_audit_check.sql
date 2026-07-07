-- Validate prune/archive audit tables and indexes
SELECT table_schema, table_name
FROM information_schema.tables
WHERE (table_schema = 'app' AND table_name = 'prune_audit')
   OR (table_schema = 'archive' AND table_name = 'prune_archive_audit')
ORDER BY table_schema, table_name;

SELECT tc.table_schema, tc.table_name, tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE (tc.table_schema = 'app' AND tc.table_name = 'prune_audit')
   OR (tc.table_schema = 'archive' AND tc.table_name = 'prune_archive_audit')
ORDER BY tc.table_schema, tc.table_name, tc.constraint_type, tc.constraint_name;

SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE (schemaname = 'app' AND tablename = 'prune_audit')
   OR (schemaname = 'archive' AND tablename = 'prune_archive_audit')
ORDER BY schemaname, tablename, indexname;
