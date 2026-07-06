-- Rollback 20260705_005: drop completed_trades table
DELETE FROM app.traderie_migrations WHERE version = 20260705_005;
DROP TABLE IF EXISTS app.completed_trades CASCADE;
