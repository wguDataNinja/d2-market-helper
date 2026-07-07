SET ROLE traderie_owner;

-- 20260706_016_seed_traderie_reference_data.sql
-- Reference rows needed by metrics and aggregate generation. No trade history.

INSERT INTO app.sources (source_id, name, source_type, category, priority, status, base_url, enabled) VALUES
    ('traderie', 'Traderie API', 'api', 'completed_player_trades', 'tier_1', 'integrated', 'https://traderie.com/api/diablo2resurrected/listings', true)
ON CONFLICT (source_id) DO NOTHING;

INSERT INTO app.rune_registry (rune_id, name, short_name, tier, in_game_key, tools_key, cash_key, cash_slug) VALUES
    (1, 'El Rune', 'El', 'low', 'El', 'El Rune', 'El', 'el_rune'),
    (2, 'Eld Rune', 'Eld', 'low', 'Eld', 'Eld Rune', 'Eld', 'eld_rune'),
    (3, 'Tir Rune', 'Tir', 'low', 'Tir', 'Tir Rune', 'Tir', 'tir_rune'),
    (4, 'Nef Rune', 'Nef', 'low', 'Nef', 'Nef Rune', 'Nef', 'nef_rune'),
    (5, 'Eth Rune', 'Eth', 'low', 'Eth', 'Eth Rune', 'Eth', 'eth_rune'),
    (6, 'Ith Rune', 'Ith', 'low', 'Ith', 'Ith Rune', 'Ith', 'ith_rune'),
    (7, 'Tal Rune', 'Tal', 'low', 'Tal', 'Tal Rune', 'Tal', 'tal_rune'),
    (8, 'Ral Rune', 'Ral', 'low', 'Ral', 'Ral Rune', 'Ral', 'ral_rune'),
    (9, 'Ort Rune', 'Ort', 'low', 'Ort', 'Ort Rune', 'Ort', 'ort_rune'),
    (10, 'Thul Rune', 'Thul', 'low', 'Thul', 'Thul Rune', 'Thul', 'thul_rune'),
    (11, 'Amn Rune', 'Amn', 'low', 'Amn', 'Amn Rune', 'Amn', 'amn_rune'),
    (12, 'Sol Rune', 'Sol', 'low', 'Sol', 'Sol Rune', 'Sol', 'sol_rune'),
    (13, 'Shael Rune', 'Shael', 'low', 'Shael', 'Shael Rune', 'Shael', 'shael_rune'),
    (14, 'Dol Rune', 'Dol', 'low', 'Dol', 'Dol Rune', 'Dol', 'dol_rune'),
    (15, 'Hel Rune', 'Hel', 'low', 'Hel', 'Hel Rune', 'Hel', 'hel_rune'),
    (16, 'Io Rune', 'Io', 'medium', 'Io', 'Io Rune', 'Io', 'io_rune'),
    (17, 'Lum Rune', 'Lum', 'medium', 'Lum', 'Lum Rune', 'Lum', 'lum_rune'),
    (18, 'Ko Rune', 'Ko', 'medium', 'Ko', 'Ko Rune', 'Ko', 'ko_rune'),
    (19, 'Fal Rune', 'Fal', 'medium', 'Fal', 'Fal Rune', 'Fal', 'fal_rune'),
    (20, 'Lem Rune', 'Lem', 'medium', 'Lem', 'Lem Rune', 'Lem', 'lem_rune'),
    (21, 'Pul Rune', 'Pul', 'medium', 'Pul', 'Pul Rune', 'Pul', 'pul_rune'),
    (22, 'Um Rune', 'Um', 'medium', 'Um', 'Um Rune', 'Um', 'um_rune'),
    (23, 'Mal Rune', 'Mal', 'medium', 'Mal', 'Mal Rune', 'Mal', 'mal_rune'),
    (24, 'Ist Rune', 'Ist', 'medium', 'Ist', 'Ist Rune', 'Ist', 'ist_rune'),
    (25, 'Gul Rune', 'Gul', 'medium', 'Gul', 'Gul Rune', 'Gul', 'gul_rune'),
    (26, 'Vex Rune', 'Vex', 'high', 'Vex', 'Vex Rune', 'Vex', 'vex_rune'),
    (27, 'Ohm Rune', 'Ohm', 'high', 'Ohm', 'Ohm Rune', 'Ohm', 'ohm_rune'),
    (28, 'Lo Rune', 'Lo', 'high', 'Lo', 'Lo Rune', 'Lo', 'lo_rune'),
    (29, 'Sur Rune', 'Sur', 'high', 'Sur', 'Sur Rune', 'Sur', 'sur_rune'),
    (30, 'Ber Rune', 'Ber', 'high', 'Ber', 'Ber Rune', 'Ber', 'ber_rune'),
    (31, 'Jah Rune', 'Jah', 'high', 'Jah', 'Jah Rune', 'Jah', 'jah_rune'),
    (32, 'Cham Rune', 'Cham', 'high', 'Cham', 'Cham Rune', 'Cham', 'cham_rune'),
    (33, 'Zod Rune', 'Zod', 'high', 'Zod', 'Zod Rune', 'Zod', 'zod_rune')
ON CONFLICT (rune_id) DO NOTHING;

INSERT INTO app.traderie_migrations (version, name, checksum_sha256, duration_ms)
VALUES (16, '20260706_016_seed_traderie_reference_data', 'placeholder-checksum', 0)
ON CONFLICT (version) DO NOTHING;

RESET ROLE;
