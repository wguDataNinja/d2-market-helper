-- Validate completed_trades table structure and constraints
SELECT column_name, data_type, is_nullable FROM information_schema.columns
WHERE table_schema = 'app' AND table_name = 'completed_trades'
ORDER BY ordinal_position;

-- Validate unique index exists
SELECT indexname FROM pg_indexes WHERE tablename = 'completed_trades' AND indexdef LIKE '%UNIQUE%';
