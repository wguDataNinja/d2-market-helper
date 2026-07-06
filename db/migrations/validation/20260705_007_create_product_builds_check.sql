-- Validate product_builds table
SELECT column_name, data_type FROM information_schema.columns
WHERE table_schema = 'app' AND table_name = 'product_builds'
ORDER BY ordinal_position;
