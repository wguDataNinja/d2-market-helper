-- Validate price_entries table
SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'app' AND table_name = 'price_entries') AS price_entries_exists;

-- Check foreign key exists
SELECT tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'app' AND tc.table_name = 'price_entries';
