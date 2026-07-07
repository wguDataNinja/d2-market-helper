-- Validate collection_run_metrics accepted design
SELECT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'app'
      AND table_name = 'collection_run_metrics'
) AS collection_run_metrics_exists;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'app'
  AND table_name = 'collection_run_metrics'
  AND column_name IN (
      'run_id',
      'snapshot_run_id',
      'workflow',
      'source_id',
      'source_slug',
      'segment_slug',
      'trigger_type',
      'started_at',
      'completed_at',
      'elapsed_ms',
      'requests_made',
      'response_bytes',
      'records_returned',
      'records_new',
      'records_skipped_duplicate',
      'duplicate_ratio',
      'retries',
      'failures',
      'stop_reason',
      'collector_version',
      'error_summary',
      'source_diagnostics',
      'segment_breakdown',
      'created_at'
  )
ORDER BY ordinal_position;

SELECT tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'app'
  AND tc.table_name = 'collection_run_metrics'
ORDER BY tc.constraint_type, tc.constraint_name;

SELECT indexname
FROM pg_indexes
WHERE schemaname = 'app'
  AND tablename = 'collection_run_metrics'
ORDER BY indexname;
