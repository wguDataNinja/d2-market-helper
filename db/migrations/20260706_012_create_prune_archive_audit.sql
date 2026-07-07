SET ROLE traderie_owner;

-- 20260706_012_create_prune_archive_audit.sql
-- Audit records for bounded pruning and archive operations.

CREATE TABLE IF NOT EXISTS app.prune_audit (
    prune_audit_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug         text NOT NULL REFERENCES app.segments(segment_slug),
    observation_key      text,
    trade_observation_id uuid REFERENCES app.completed_trades(trade_observation_id) ON DELETE SET NULL,
    action               text NOT NULL CHECK (action IN ('planned', 'archived', 'pruned', 'restored', 'skipped')),
    reason_code          text NOT NULL,
    source_table         text NOT NULL,
    archive_table        text,
    acted_at             timestamptz NOT NULL DEFAULT now(),
    acted_by             text NOT NULL DEFAULT current_user,
    metadata             jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS archive.prune_archive_audit (
    prune_archive_audit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    segment_slug           text NOT NULL,
    observation_key        text,
    source_table           text NOT NULL,
    archived_payload       jsonb NOT NULL,
    archived_at            timestamptz NOT NULL DEFAULT now(),
    archived_by            text NOT NULL DEFAULT current_user,
    metadata               jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_prune_audit_segment_action
    ON app.prune_audit(segment_slug, action, acted_at DESC);
CREATE INDEX IF NOT EXISTS idx_prune_audit_observation_key
    ON app.prune_audit(segment_slug, observation_key)
    WHERE observation_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_prune_audit_trade
    ON app.prune_audit(trade_observation_id)
    WHERE trade_observation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_prune_archive_audit_segment_archived
    ON archive.prune_archive_audit(segment_slug, archived_at DESC);
CREATE INDEX IF NOT EXISTS idx_prune_archive_audit_observation_key
    ON archive.prune_archive_audit(segment_slug, observation_key)
    WHERE observation_key IS NOT NULL;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (12, '20260706_012_create_prune_archive_audit', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
