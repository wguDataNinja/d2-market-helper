# D2R Market Helper — Internal Repo Spec

**Generated:** 2026-06-23
**Purpose:** Complete inventory of the repo for code review, handoff, and decision tracking.

---

## 1. Product Definition

Multi-source market intelligence hub for Diablo II: Resurrected traders. Two data tracks:
- **In-game barter value** (Traderie completed trades, Ist-normalized VWAP)
- **External cash comparison** (5 cash market sources, comparison-only, `use_in_model=false`)

**Core rules:** Never blend cash into in-game values. Never merge economy segments (PC SC L, PC SC NL, PC HC L, PC HC NL). Every value carries segment, source, evidence class, and confidence.

---

## 2. Pipeline Architecture

### Data Flow

```
Traderie API → snapshot_traderie.py → raw/normalized snapshots → history JSONL
History JSONL → build_traderie_dataset_from_history.py → research CSVs
Research CSVs → calculate_rune_prices.py → per-segment price CSVs
Price CSVs → generate_prices_json.py → in_game_rune_values.json + traderie_tools_prices.json

Cash sources → parse_*.py → external/*_cash_prices.json
generate_external_cash_prices.py → external_cash_prices.sample.json
```

### Key Scripts

| Script | Role |
|--------|------|
| `scripts/snapshot_traderie.py` | Primary collector — 4 segments × ~70 items, 4x daily via launchd. Writes snapshots + history. |
| `scripts/fetch_completed_trades.py` | Legacy collector (no snapshot/history). Kept for backward compat. |
| `scripts/build_traderie_dataset_from_history.py` | Builds extracted trade CSVs from retained history JSONL. Dedupes by listing_id. |
| `scripts/calculate_rune_prices.py` | Ist-normalized VWAP with bid/ask separation. Decomposes 2-item AND trades into model rows. |
| `scripts/generate_prices_json.py` | Produces 3 output products from per-segment CSVs. |
| `scripts/generate_external_cash_prices.py` | Merges per-source cash files → single normalized product. |
| `scripts/collection_status.py` | Read-only health report — history rows, snapshot age, launchd logs. |
| `scripts/validate_source_manifest.py` | Validates all 20 sources in manifest. |
| `scripts/validate_in_game_rune_values.py` | Schema/content validation for in-game product. |
| `scripts/validate_external_cash_prices.py` | Schema/content validation for cash product. |
| `scripts/regenerate_products.sh` | Full pipeline runner for launchd. |

### Cash Parsers

| Parser | Source | Method | Observations |
|--------|--------|--------|-------------|
| `parse_iggm_offline.py` | IGGM | Regex on browser-captured HTML | 30 |
| `parse_itemnow_api.py` | ItemNow | WooCommerce Store API | 42 |
| `parse_d2stock_rss.py` | D2Stock | RSS/XML feed | 199 |
| `parse_items7_offline.py` | items7 | Static HTML (no prices — blocked) | 0 |
| `parse_mulefactory.py` | MuleFactory | Schema.org microdata via extruct | 24 |
| `parse_diablo2io_sold_search_offline.py` | Diablo2.io | Static HTML fixture (research only) | 14 |

---

## 3. Current Product State

### In-Game Rune Values (`in_game_rune_values.json`)

| Segment | Modeled Trades | Runes Tracked | High Conf | Medium Conf | Low Conf | Unavailable |
|---------|---------------|---------------|-----------|-------------|----------|-------------|
| pc_sc_l | 1,319 | 23 | 6 | 1 | 4 | 12 |
| pc_sc_nl | 569 | 23 | 2 | 4 | 6 | 11 |
| pc_hc_l | 65 | 23 | 0 | 1 | 6 | 16 |
| pc_hc_nl | 38 | 23 | 0 | 0 | 9 | 14 |
| **Total** | **1,991** | **92** | **8** | **6** | **25** | **53** |

Key rune values (pc_sc_l): Ber=18.04 Ist (high), Jah=11.74 Ist (high), Lo=5.90 Ist (high), Ohm=3.41 Ist (high), Gul=1.01 Ist (high), Mal=0.72 Ist (high).

### External Cash Prices (`external_cash_prices.sample.json`)

| Source | Observations | Price Range |
|--------|-------------|-------------|
| IGGM | 30 | $0.09 – $8.99 |
| ItemNow | 42 | $0.05 – $43.50 |
| D2Stock | 199 | $0.31 – $94.45 |
| MuleFactory | 24 | $0.35 – $3.13 |
| items7 | 0 | — |
| **Total** | **295** | |

### Data Files

| File | Status |
|------|--------|
| `data/products/in_game_rune_values.json` | Active — v0.1, 1991 trades, 92 runes, 4 segments |
| `data/products/traderie_tools_prices.json` | Active — v0.2, userscript-compatible |
| `data/products/external_cash_prices.sample.json` | Active — v0.2, 5 sources, 295 obs |
| `data/products/rune_prices_legacy.json` | Active — flat format for legacy userscript |
| `data/rune_registry.json` | Active — 33 runes, id 1-33, name crosswalk |
| `data/source_manifest.json` | Active — 20 sources, all validated |
| `data/item_ids.json` | Active — ~70 items (runes, keys, selected uniques) |

---

## 4. Source Manifest (20 Sources)

| Source | Status | Priority | Role |
|--------|--------|----------|------|
| Traderie | integrated | tier_1 | Canonical completed-trade source |
| IGGM | parser_prototype_ready | tier_2 | Cash comparison (30 obs) |
| ItemNow | parser_prototype_ready | tier_3 | Cash comparison (42 obs) |
| D2Stock | parser_prototype_ready | tier_2 | Cash comparison (199 obs) |
| MuleFactory | parser_prototype_ready | tier_3 | Cash comparison (24 obs) |
| Diablo2.io | parser_prototype_ready | tier_1 (caveated) | Research: 14 rows, not integrated |
| Eldorado | captured_browser | tier_3 | Cash (476 listings, rendered HTML) |
| MMOPixel | captured_browser | later | Cash (1,304 items, rendered) |
| PlayerAuctions | captured_browser | tier_3 | Cash — no sold surface, deferred |
| G2G | captured_browser | tier_2 | Cash — LoD vs ROTW tax unresolved |
| items7 | captured_static | tier_3 | 0 parseable rows — browser needed |
| Odealo | captured_browser | tier_3 | Cash — React app, needs capture |
| AOEAH | captured_static | tier_3 | Cash — CSS-styled prices |
| Chicks Gold | captured_static | later | Cash — fully dynamic, low priority |
| YesGamers | deferred | tier_3 | Login wall |
| d2jsp | deferred | later | Fully gated (Cloudflare + login) |
| Reddit | deferred | tier_3 | Qualitative only |
| eBay | deferred | later | Anti-bot blocks automation |
| RPGStash | discovered | later | Camoufox crashes |
| Discord/Baal's Ledger | discovered | later | Gated/manual |

---

## 5. Recent Work (Roadmap Sessions 1-6)

### Session 1 — Doc Refresh
- `docs/PROJECT_MEMORY.md` Section 10 replaced → points at ROADMAP.md
- `docs/COLLECTION_RUNBOOK.md` — 2× stale snapshot_io notes replaced
- `docs/DATA_PRODUCTS.md` — counts updated (2,570→1,151 modeled trades)
- `data/source_manifest.json` — d2stock→parser_prototype_ready, iggm/itemnow next_action updated

### Session 2 — AND Trade Decomposition
- **Decision:** Approach B — include AND trades, cap at 2-item requests, flag for audit
- Modified `build_traderie_dataset_from_history.py`: added `requested_groups` + `price_groups_json` column
- Modified `calculate_rune_prices.py`: decomposes 2-colon Requested strings into per-item rows with `is_and_decomposed` flag
- Modified `generate_prices_json.py`: caveats updated
- **Impact:** 1,151 → 1,991 modeled trades (+73%)
- **Decomposed:** 1,384 AND rows; **Excluded (>2 items):** 232

### Session 3 — MuleFactory Cash Parser
- Created `scripts/parse_mulefactory.py` — extruct-based Schema.org microdata extraction
- 24 rune observations from static HTML fixture
- Added to generator inputs + caveats
- **Total cash observations:** 271 → 295

### Session 4 — Operational Hardening
- Created `scripts/regenerate_products.sh` — full pipeline runner (venv-aware)
- Created `launchd/com.buddy.traderie.regenerate-products.plist` — daily 06:00
- **Decision:** Option B (separate daily job, com.buddy.traderie namespace)
- Both plists validated with `plutil -lint`

### Session 5 — Hardcore Gap Probe
- Probed all 9 pc_hc_nl skipped items with skip list temporarily cleared
- **Result:** 8/9 items → ReadTimeout on both retry attempts (88.9% failure)
- Ist Rune succeeded (1 ReadTimeout → retry → 50 listings)
- Root cause: Traderie API hangs (ReadTimeout, not HTTP error) when zero completed listings exist for that item+segment
- **Decision:** Restored skip list (Option A — maintain)

### Session 6 — Validation & Cleanup
- Full validation suite: ✅ all pass
- Web build: ✅ (chunk size warning only)
- Old remnants cleaned from ROADMAP.md → moved to BACKLOG.md
- BACKLOG.md created: 6 deferred items
- LOG.md finalized with all HITL decisions

---

## 6. Pipeline Constraints & Known Issues

### Traderie API
- **50-listing cap:** `completed=true` returns max 50 listings per item/segment. No real pagination — `nextPage` is a boolean flag, not a cursor.
- **No timestamps:** No `created_at`/`completed_at`. Only `updated_at`. History built via scheduled polling.
- **No buyer field:** Only seller data exposed.
- **AND trade groups:** Raw API tracks price groups (the `group` field) but the current decomposition uses Requested string parsing. The `price_groups_json` column in the CSV preserves the raw group structure for audit.
- **Hardcore instability:** pc_hc_nl has 9 items permanently skipped (API hangs — zero listings). pc_hc_l has thin but usable volume.
- **Timeout config:** 20s for hardcore, 10s for softcore. Up to 2 retries with backoff.

### Cash Sources
- All prices are **asking prices** — not completed sales
- Segment metadata is source-dependent and often unverified
- MuleFactory: 24 of 33 runes only (page 1); remaining paginated via AJAX
- D2Stock: best coverage (199 obs, segment-specific from RSS feed titles)
- items7: fully blocked — browser capture required

### Model
- Ist-normalized VWAP only — non-Ist rune pairs excluded
- AND trades with >2 items excluded (confirmed decision, 232 skipped)
- No multi-source in-game model yet (Diablo2.io has only 14 rows)
- No buyer side — all confidence is from trade count, not trade quality
- Confidence thresholds: high ≥50, medium 15-49, low 1-14

---

## 7. Operational State

### Launchd Jobs

| Label | Schedule | Runner | Status |
|-------|----------|--------|--------|
| `com.buddy.traderie.snapshot-traderie` | 05:00 / 11:00 / 17:00 / 23:00 | `run_traderie_snapshot_launchd.sh` | Installed, loaded |
| `com.buddy.traderie.regenerate-products` | 06:00 daily | `regenerate_products.sh` | Plist at `launchd/`, not yet installed |

### Snapshot/History Volume

| Source | History Size |
|--------|-------------|
| Traderie pc_sc_l | 19,200 rows (7,484 unique) |
| Traderie pc_sc_nl | 19,300 rows (4,045 unique) |
| Traderie pc_hc_l | 19,580 rows (2,025 unique) |
| Traderie pc_hc_nl | 9,508 rows (1,096 unique) |
| MuleFactory | 2 snapshots |
| ItemNow | 3 snapshots |

### Ignored Paths
`.gitignore` covers: `data/snapshots/`, `data/history/`, `logs/`, `.run/`, `data/raw/`, `data/extracted/`, `.venv/`, `web/dist/`, `web/node_modules/`, `*.har`, `data/research/`, `research/sources/captures/`.

### Lock
Atomic `mkdir` lock at `.run/locks/snapshot-traderie.lock`. Auto-released via `trap`.

---

## 8. Web Dashboard

**Stack:** Vite 8 + React 19 + TypeScript + react-router-dom
**Directory:** `web/`
**Pages:**
- `/` — Market overview
- `/runes` — Full dashboard (configurable segment)
- `/sources` — Source directory
- `/about-methodology` — Methodology docs

**Features:**
- Segment selector via URL query param (`?segment=pc_sc_nl`)
- All 4 PC segments supported
- In-game and cash columns visually distinct with disclaimer
- Source freshness indicators
- Confidence tooltips
- Responsive layout

---

## 9. HITL Decision Log

| Session | Decision | Rationale |
|---------|----------|-----------|
| 1 | Review checkpoint | No decision — doc refresh validation |
| 2 | B — Include AND trades, cap at 2 | 24.6% of trades are AND; avg group size ~2; proportional decomposition is reasonable |
| 3 | Review checkpoint | No decision — parser output review |
| 4 | B — Separate daily launchd job | Cleaner than extending snapshot plist; `com.buddy.traderie` namespace isolates from other repos |
| 5 | A — Maintain skip list | 88.9% failure rate confirms API hangs for items with zero listings on pc_hc_nl |

---

## 10. Backlog (from BACKLOG.md)

- Eldorado.gg rendered-HTML parser (tier_3, low effort)
- Odealo rune-page capture + parser (tier_3, needs browser capture)
- AOEAH CSS-aware extraction (tier_3, low priority)
- Diablo2.io price-history probe (research-only, low volume)
- Item profiles display on web (5 profiles exist, not surfaced)
- Console segment discovery (PS/Xbox/Switch, not started)

---

## 11. File Map

### Root
| File | Purpose |
|------|---------|
| `ROADMAP.md` | Active task authority — Sessions 1-6 complete |
| `AGENTS.md` | Agent operating contract and routing |
| `SESSION.md` | Current session tracking |
| `LOG.md` | Persistent commit/deployment log |
| `BACKLOG.md` | Deferred/candidate work items |

### Scripts
| File | Purpose |
|------|---------|
| `scripts/__init__.py` | Package init |
| `scripts/lib/` | Shared library (snapshot_io, etc.) |
| `scripts/snapshot_traderie.py` | Primary collector |
| `scripts/fetch_completed_trades.py` | Legacy collector |
| `scripts/build_traderie_dataset_from_history.py` | History → CSV builder |
| `scripts/calculate_rune_prices.py` | VWAP calculator |
| `scripts/generate_prices_json.py` | Product generator (in-game) |
| `scripts/generate_external_cash_prices.py` | Product generator (cash) |
| `scripts/collection_status.py` | Health reporter |
| `scripts/parse_d2stock_rss.py` | D2Stock RSS parser |
| `scripts/parse_iggm_offline.py` | IGGM HTML parser |
| `scripts/parse_itemnow_api.py` | ItemNow API parser |
| `scripts/parse_mulefactory.py` | MuleFactory microdata parser |
| `scripts/parse_items7_offline.py` | items7 parser (blocked) |
| `scripts/parse_diablo2io_sold_search_offline.py` | Diablo2.io research parser |
| `scripts/extract_rune_trades.py` | Legacy extractor |
| `scripts/regenerate_products.sh` | Full pipeline shell runner |
| `scripts/run_traderie_snapshot_launchd.sh` | Launchd snapshot runner |
| `scripts/validate_source_manifest.py` | Manifest validator |
| `scripts/validate_in_game_rune_values.py` | In-game product validator |
| `scripts/validate_external_cash_prices.py` | Cash product validator |
| `scripts/validate_item_profiles.py` | Item profile validator |
| `scripts/audit_traderie_pagination.py` | Pagination behavior tester |
| `scripts/audit_traderie_raw_fetch.py` | Raw response inspector |
| `scripts/test_userscript_parse.py` | Userscript test harness |
| `scripts/capture_with_camoufox.py` | Camoufox browser capture |
| `scripts/capture_source_smoke.py` | Source smoke test capture |
| `scripts/capture_diablo2io_fixtures.py` | Diablo2.io fixture capture |
| `scripts/capture_iggm_rune_focused.py` | IGGM capture helper |
| `scripts/capture_g2g_page.py` | G2G capture helper |
| `scripts/capture_g2g_preview.py` | G2G preview capture |
| `scripts/reddit_extract_items.py` | Reddit research |
| `scripts/rune_value_normalization_v4.py` | Legacy normalization |
| `scripts/check_file_sizes.py` | File size audit |

### Docs
| File | Purpose |
|------|---------|
| `docs/PROJECT_MEMORY.md` | Complete project state and history |
| `docs/COLLECTION_RUNBOOK.md` | Collection scheduling and runbook |
| `docs/DATA_PRODUCTS.md` | Data product schemas and docs |
| `docs/PRICING_MODEL.md` | Pricing model documentation |
| `docs/ARCHITECTURE.md` | System architecture |
| `docs/SOURCE_MANIFEST.md` | Source discovery documentation |
| `docs/SOURCE_DISCOVERY.md` | Source discovery process |
| `docs/USERSCRIPT.md` | Userscript integration docs |
| `docs/OVERLAY_FEED_CONTRACT.md` | Overlay feed contract |
| `docs/TRADERIE_COMPLETED_TRADES_AUDIT.md` | Traderie API audit |
| `docs/TRADERIE_NORMALIZED_SCHEMA.md` | Normalized schema docs |
| `docs/TRADERIE_OVERLAY_PATCH_PLAN.md` | Overlay patch plan |
| `docs/TRADERIE_TOOLS_INTEGRATION.md` | Userscript integration |
| `docs/LAUNCHD_SETUP.md` | Launchd setup guide |
| `docs/ITEM_PROFILES.md` | Item profile definitions |
| `docs/ITEM_REGISTRY.md` | Item registry docs |
| `docs/MARKET_RESEARCH.md` | Market research notes |
| `docs/REDDIT_RESEARCH_PLAN.md` | Reddit research plan |
| `docs/CODEX_HANDOFF.md` | Codex handoff packet |
| `docs/REPO_SPEC.md` | This file |
