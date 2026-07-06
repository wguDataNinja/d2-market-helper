-- Rollback 20260705_007: drop product_builds table
DELETE FROM app.traderie_migrations WHERE version = 20260705_007;
DROP TABLE IF EXISTS app.product_builds CASCADE;
