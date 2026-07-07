-- Validate external Traderie ID columns are bigint.

SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'app'
  AND (
    (table_name = 'items' AND column_name = 'item_id')
    OR (table_name = 'completed_trades' AND column_name IN ('listing_id', 'item_id'))
    OR (table_name = 'price_entries' AND column_name IN ('requested_item_id', 'rune_item_id'))
  )
ORDER BY table_name, column_name;
