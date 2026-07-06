-- Validate snapshot_runs table
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema = 'app' AND table_name = 'snapshot_runs'
ORDER BY ordinal_position;
