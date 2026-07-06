-- Rollback 20260705_008: drop rune tables
DELETE FROM app.traderie_migrations WHERE version = 20260705_008;
DROP TABLE IF EXISTS app.ruleset_breakdowns CASCADE;
DROP TABLE IF EXISTS app.segment_rune_prices CASCADE;
DROP TABLE IF EXISTS app.rune_registry CASCADE;
