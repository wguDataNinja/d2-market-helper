-- Validate segment_aggregates accepted hourly/daily price-history design
SELECT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'app'
      AND table_name = 'segment_aggregates'
) AS segment_aggregates_exists;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'app'
  AND table_name = 'segment_aggregates'
  AND column_name IN (
      'aggregate_id',
      'bucket_start',
      'bucket_end',
      'source_id',
      'source_slug',
      'segment_slug',
      'rune_id',
      'granularity',
      'observation_count',
      'trade_count',
      'volume_total',
      'vwap',
      'median_price',
      'min_price',
      'max_price',
      'first_seen_at',
      'last_seen_at',
      'run_id',
      'generation_metadata',
      'created_at'
  )
ORDER BY ordinal_position;

SELECT tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'app'
  AND tc.table_name = 'segment_aggregates'
ORDER BY tc.constraint_type, tc.constraint_name;

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'app'
  AND tablename = 'segment_aggregates'
ORDER BY indexname;
