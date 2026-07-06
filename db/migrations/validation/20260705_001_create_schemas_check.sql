-- Validate schemas exist
SELECT 'app' AS schema_name FROM information_schema.schemata WHERE schema_name = 'app'
UNION ALL
SELECT 'health' FROM information_schema.schemata WHERE schema_name = 'health'
UNION ALL
SELECT 'archive' FROM information_schema.schemata WHERE schema_name = 'archive';

-- Validate migration table exists
SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'app' AND table_name = 'traderie_migrations') AS migration_table_exists;
