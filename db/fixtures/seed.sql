-- db/fixtures/seed.sql
-- Small synthetic fixture data for local validation.
-- No real Traderie data. All values are fabricated.

-- Items (subset of rune_registry mapped to app.items)
INSERT INTO app.items (item_id, name, category, short_name, tier) VALUES
    (2290642411, 'Ist Rune',  'rune', 'Ist', 'medium'),
    (2552039455, 'Jah Rune',  'rune', 'Jah', 'high'),
    (4149485449, 'Ber Rune',  'rune', 'Ber', 'high'),
    (3896329590, 'Ohm Rune',  'rune', 'Ohm', 'high'),
    (3632079454, 'Lo Rune',   'rune', 'Lo',  'high'),
    (2401638276, 'Mal Rune',  'rune', 'Mal', 'medium'),
    (4160776515, 'Gul Rune',  'rune', 'Gul', 'medium')
ON CONFLICT (item_id) DO NOTHING;

-- Sources (minimal set)
INSERT INTO app.sources (source_id, name, source_type, category, priority, status, base_url, enabled) VALUES
    ('traderie',   'Traderie API',            'api',    'completed_player_trades', 'tier_1', 'integrated',              'https://traderie.com/api/diablo2resurrected/listings', true),
    ('iggm',       'IGGM',                    'parser', 'cash_market',             'tier_2', 'parser_prototype_ready', 'https://www.iggm.com/diablo-2-resurrected-items',      false),
    ('d2stock',    'D2Stock',                 'parser', 'cash_market',             'tier_2', 'parser_prototype_ready', 'https://d2stock.com/',                                 false),
    ('diablo2_io', 'Diablo2.io',              'parser', 'completed_player_trades', 'tier_1', 'parser_prototype_ready', 'https://diablo2.io/',                                  false)
ON CONFLICT (source_id) DO NOTHING;

-- Snapshot runs
INSERT INTO app.snapshot_runs (snapshot_run_id, segment_slug, run_timestamp, status, item_count, listing_count, duration_seconds) VALUES
    ('11111111-1111-1111-1111-111111111111', 'pc_sc_l',  '2026-07-05T05:00:00Z', 'completed', 25, 1250, 300),
    ('22222222-2222-2222-2222-222222222222', 'pc_sc_nl', '2026-07-05T05:00:00Z', 'completed', 25, 980,  280),
    ('33333333-3333-3333-3333-333333333333', 'pc_hc_l',  '2026-07-05T05:00:00Z', 'completed', 25, 420,  350),
    ('44444444-4444-4444-4444-444444444444', 'pc_hc_nl', '2026-07-05T05:00:00Z', 'partial',   25, 85,   400)
ON CONFLICT (snapshot_run_id) DO NOTHING;

-- Completed trades (synthetic)
INSERT INTO app.completed_trades (trade_observation_id, segment_slug, observation_key, listing_id, content_hash, item_id, item_name, quantity, captured_at, ruleset, has_and_prices, price_group_count, price_entry_count, snapshot_run_id) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'pc_sc_l', 'traderie/pc_sc_l::Ist Rune::2.5::2026-07-05T05:00:00Z::1001', 1001, 'sha256-a1', 2290642411, 'Ist Rune', 1, '2026-07-05T05:00:00Z', 'rotw', false, 1, 1, '11111111-1111-1111-1111-111111111111'),
    ('a0000000-0000-0000-0000-000000000002', 'pc_sc_l', 'traderie/pc_sc_l::Jah Rune::17.0::2026-07-05T05:00:00Z::1002', 1002, 'sha256-a2', 2552039455, 'Jah Rune', 1, '2026-07-05T05:00:00Z', 'rotw', false, 1, 1, '11111111-1111-1111-1111-111111111111'),
    ('a0000000-0000-0000-0000-000000000003', 'pc_sc_l', 'traderie/pc_sc_l::Ber Rune::15.5::2026-07-05T05:00:00Z::1003', 1003, 'sha256-a3', 4149485449, 'Ber Rune', 1, '2026-07-05T05:00:00Z', 'rotw', false, 1, 1, '11111111-1111-1111-1111-111111111111'),
    ('a0000000-0000-0000-0000-000000000004', 'pc_sc_nl','traderie/pc_sc_nl::Ist Rune::2.0::2026-07-05T05:00:00Z::2001', 2001, 'sha256-b1', 2290642411, 'Ist Rune', 1, '2026-07-05T05:00:00Z', 'lod',  false, 1, 1, '22222222-2222-2222-2222-222222222222'),
    ('a0000000-0000-0000-0000-000000000005', 'pc_sc_nl','traderie/pc_sc_nl::Ohm Rune::3.2::2026-07-05T05:00:00Z::2002', 2002, 'sha256-b2', 3896329590, 'Ohm Rune', 1, '2026-07-05T05:00:00Z', 'rotw', false, 1, 1, '22222222-2222-2222-2222-222222222222'),
    ('a0000000-0000-0000-0000-000000000006', 'pc_hc_l', 'traderie/pc_hc_l::Mal Rune::0.5::2026-07-05T05:00:00Z::3001', 3001, 'sha256-c1', 2401638276, 'Mal Rune', 1, '2026-07-05T05:00:00Z', 'classic', false, 1, 1, '33333333-3333-3333-3333-333333333333'),
    ('a0000000-0000-0000-0000-000000000007', 'pc_hc_nl','traderie/pc_hc_nl::Gul Rune::1.0::2026-07-05T05:00:00Z::4001', 4001, 'sha256-d1', 4160776515, 'Gul Rune', 1, '2026-07-05T05:00:00Z', 'unknown', false, 1, 1, '44444444-4444-4444-4444-444444444444')
ON CONFLICT (trade_observation_id) DO NOTHING;

-- Price entries (synthetic)
INSERT INTO app.price_entries (price_entry_id, trade_id, requested_item_id, item_name, quantity, add_flag, group_number) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 2290642411, 'Ist Rune', 2, false, 0),
    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000002', 2290642411, 'Ist Rune', 17, false, 0),
    ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000003', 2290642411, 'Ist Rune', 15, false, 0),
    ('b0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000004', 2290642411, 'Ist Rune', 2, false, 0),
    ('b0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000005', 2290642411, 'Ist Rune', 3, false, 0),
    ('b0000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000006', 2290642411, 'Ist Rune', 1, false, 0),
    ('b0000000-0000-0000-0000-000000000007', 'a0000000-0000-0000-0000-000000000007', 2290642411, 'Ist Rune', 1, false, 0)
ON CONFLICT (price_entry_id) DO NOTHING;

-- Product builds
INSERT INTO app.product_builds (build_id, segment_slug, generated_at, status, schema_version, total_trades, unique_listings) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'pc_sc_l',  '2026-07-05T10:00:00Z', 'completed', '0.1', 1250, 850),
    ('c0000000-0000-0000-0000-000000000002', 'pc_sc_nl', '2026-07-05T10:00:00Z', 'completed', '0.1', 980,  620),
    ('c0000000-0000-0000-0000-000000000003', 'pc_hc_l',  '2026-07-05T10:00:00Z', 'completed', '0.1', 420,  180),
    ('c0000000-0000-0000-0000-000000000004', 'pc_hc_nl', '2026-07-05T10:00:00Z', 'completed', '0.1', 85,   42)
ON CONFLICT (build_id) DO NOTHING;

-- Rune registry (33 runes)
INSERT INTO app.rune_registry (rune_id, name, short_name, tier, in_game_key, tools_key, cash_key, cash_slug) VALUES
    (1,  'El Rune',   'El',   'low',    'El',   'El Rune',   'El',   'el_rune'),
    (2,  'Eld Rune',  'Eld',  'low',    'Eld',  'Eld Rune',  'Eld',  'eld_rune'),
    (3,  'Tir Rune',  'Tir',  'low',    'Tir',  'Tir Rune',  'Tir',  'tir_rune'),
    (4,  'Nef Rune',  'Nef',  'low',    'Nef',  'Nef Rune',  'Nef',  'nef_rune'),
    (5,  'Eth Rune',  'Eth',  'low',    'Eth',  'Eth Rune',  'Eth',  'eth_rune'),
    (6,  'Ith Rune',  'Ith',  'low',    'Ith',  'Ith Rune',  'Ith',  'ith_rune'),
    (7,  'Tal Rune',  'Tal',  'low',    'Tal',  'Tal Rune',  'Tal',  'tal_rune'),
    (8,  'Ral Rune',  'Ral',  'low',    'Ral',  'Ral Rune',  'Ral',  'ral_rune'),
    (9,  'Ort Rune',  'Ort',  'low',    'Ort',  'Ort Rune',  'Ort',  'ort_rune'),
    (10, 'Thul Rune', 'Thul', 'low',    'Thul', 'Thul Rune', 'Thul', 'thul_rune'),
    (11, 'Amn Rune',  'Amn',  'low',    'Amn',  'Amn Rune',  'Amn',  'amn_rune'),
    (12, 'Sol Rune',  'Sol',  'low',    'Sol',  'Sol Rune',  'Sol',  'sol_rune'),
    (13, 'Shael Rune','Shael','low',    'Shael','Shael Rune','Shael','shael_rune'),
    (14, 'Dol Rune',  'Dol',  'low',    'Dol',  'Dol Rune',  'Dol',  'dol_rune'),
    (15, 'Hel Rune',  'Hel',  'low',    'Hel',  'Hel Rune',  'Hel',  'hel_rune'),
    (16, 'Io Rune',   'Io',   'medium', 'Io',   'Io Rune',   'Io',   'io_rune'),
    (17, 'Lum Rune',  'Lum',  'medium', 'Lum',  'Lum Rune',  'Lum',  'lum_rune'),
    (18, 'Ko Rune',   'Ko',   'medium', 'Ko',   'Ko Rune',   'Ko',   'ko_rune'),
    (19, 'Fal Rune',  'Fal',  'medium', 'Fal',  'Fal Rune',  'Fal',  'fal_rune'),
    (20, 'Lem Rune',  'Lem',  'medium', 'Lem',  'Lem Rune',  'Lem',  'lem_rune'),
    (21, 'Pul Rune',  'Pul',  'medium', 'Pul',  'Pul Rune',  'Pul',  'pul_rune'),
    (22, 'Um Rune',   'Um',   'medium', 'Um',   'Um Rune',   'Um',   'um_rune'),
    (23, 'Mal Rune',  'Mal',  'medium', 'Mal',  'Mal Rune',  'Mal',  'mal_rune'),
    (24, 'Ist Rune',  'Ist',  'medium', 'Ist',  'Ist Rune',  'Ist',  'ist_rune'),
    (25, 'Gul Rune',  'Gul',  'medium', 'Gul',  'Gul Rune',  'Gul',  'gul_rune'),
    (26, 'Vex Rune',  'Vex',  'high',   'Vex',  'Vex Rune',  'Vex',  'vex_rune'),
    (27, 'Ohm Rune',  'Ohm',  'high',   'Ohm',  'Ohm Rune',  'Ohm',  'ohm_rune'),
    (28, 'Lo Rune',   'Lo',   'high',   'Lo',   'Lo Rune',   'Lo',   'lo_rune'),
    (29, 'Sur Rune',  'Sur',  'high',   'Sur',  'Sur Rune',  'Sur',  'sur_rune'),
    (30, 'Ber Rune',  'Ber',  'high',   'Ber',  'Ber Rune',  'Ber',  'ber_rune'),
    (31, 'Jah Rune',  'Jah',  'high',   'Jah',  'Jah Rune',  'Jah',  'jah_rune'),
    (32, 'Cham Rune', 'Cham', 'high',   'Cham', 'Cham Rune', 'Cham', 'cham_rune'),
    (33, 'Zod Rune',  'Zod',  'high',   'Zod',  'Zod Rune',  'Zod',  'zod_rune')
ON CONFLICT (rune_id) DO NOTHING;

-- Segment rune prices (synthetic)
INSERT INTO app.segment_rune_prices (rune_price_id, build_id, segment_slug, rune_id, rune_name, value_ist, bid_price, ask_price, bid_count, ask_count, total_trades, confidence) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 24, 'Ist', 1.0000, 1.0000, 1.0000, 100, 100, 200, 'high'),
    ('d0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 30, 'Ber', 17.2500, 16.3900, 18.1200, 102, 118, 220, 'high'),
    ('d0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 31, 'Jah', 11.5000, 10.9300, 12.0800, 98, 112, 210, 'high'),
    ('d0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000002', 'pc_sc_nl',24, 'Ist', 1.0000, 1.0000, 1.0000, 80, 80, 160, 'high'),
    ('d0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000002', 'pc_sc_nl',30, 'Ber', 15.8000, 15.0100, 16.5900, 65, 72, 137, 'high')
ON CONFLICT (rune_price_id) DO NOTHING;

-- Ruleset breakdowns (synthetic)
INSERT INTO app.ruleset_breakdowns (breakdown_id, build_id, segment_slug, ruleset, count, pct) VALUES
    ('e0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 'rotw',    26120, 99.32),
    ('e0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 'lod',     148,    0.56),
    ('e0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 'classic', 26,     0.10),
    ('e0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000001', 'pc_sc_l', 'unknown', 6,      0.02),
    ('e0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000002', 'pc_sc_nl','rotw',    30791,  96.22),
    ('e0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000002', 'pc_sc_nl','lod',     1090,   3.41)
ON CONFLICT (breakdown_id) DO NOTHING;

-- Health runs
INSERT INTO health.health_runs (run_id, workflow, status, started_at, finished_at, last_success_at, expected_cadence, records_read, records_written, error_class) VALUES
    ('f0000000-0000-0000-0000-000000000001', 'snapshot', 'ok',   '2026-07-05T05:00:00Z', '2026-07-05T05:05:00Z', '2026-07-05T05:00:00Z', '6 hours',  1250, 1250, NULL),
    ('f0000000-0000-0000-0000-000000000002', 'product_regen', 'ok', '2026-07-05T10:00:00Z', '2026-07-05T10:02:00Z', '2026-07-05T10:00:00Z', '24 hours', 2735, 4, NULL),
    ('f0000000-0000-0000-0000-000000000003', 'backup', 'fail', '2026-07-05T11:00:00Z', NULL, '2026-07-04T11:00:00Z', '24 hours',  0, 0, 'IOError')
ON CONFLICT (run_id) DO NOTHING;
