-- Validate rune tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'app' AND table_name IN ('rune_registry', 'segment_rune_prices', 'ruleset_breakdowns')
ORDER BY table_name;
