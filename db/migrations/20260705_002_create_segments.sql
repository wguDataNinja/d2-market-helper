SET ROLE traderie_owner;

-- 20260705_002_create_segments.sql
-- Economy segments: four strictly separated PC segments.
-- See CODEX_SESSION_1_ARCHITECTURE.md §12.

CREATE TABLE IF NOT EXISTS app.segments (
    segment_slug    text PRIMARY KEY,
    display_name    text NOT NULL,
    platform        text NOT NULL DEFAULT 'pc' CHECK (platform IN ('pc')),
    mode            text NOT NULL CHECK (mode IN ('softcore', 'hardcore')),
    ladder          boolean NOT NULL,
    hardcore        boolean NOT NULL,
    enabled         boolean NOT NULL DEFAULT true,
    description     text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

INSERT INTO app.segments (segment_slug, display_name, platform, mode, ladder, hardcore, enabled, description) VALUES
    ('pc_sc_l',   'PC Softcore Ladder',   'pc', 'softcore', true,  false, true, 'PC softcore ladder economy'),
    ('pc_sc_nl',  'PC Softcore Non-Ladder','pc', 'softcore', false, false, true, 'PC softcore non-ladder economy'),
    ('pc_hc_l',   'PC Hardcore Ladder',   'pc', 'hardcore', true,  true,  true, 'PC hardcore ladder economy'),
    ('pc_hc_nl',  'PC Hardcore Non-Ladder','pc', 'hardcore', false, true,  true, 'PC hardcore non-ladder economy')
ON CONFLICT (segment_slug) DO NOTHING;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (2, '20260705_002_create_segments', 'placeholder-checksum', 0);

RESET ROLE;
