-- Validate health schema tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'health' AND table_name IN ('health_runs', 'workflow_status')
ORDER BY table_name;
