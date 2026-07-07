-- Validate Traderie reference rows needed by lifecycle scripts.

SELECT 'traderie_source_exists' AS check_name,
       CASE WHEN EXISTS (SELECT 1 FROM app.sources WHERE source_id = 'traderie')
       THEN 'PASS' ELSE 'FAIL' END AS result;

SELECT 'rune_registry_33_rows' AS check_name,
       CASE WHEN COUNT(*) = 33 THEN 'PASS' ELSE 'FAIL' END AS result,
       COUNT(*) AS row_count
FROM app.rune_registry;
