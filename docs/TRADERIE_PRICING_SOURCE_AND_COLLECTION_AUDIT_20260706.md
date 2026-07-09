# Traderie — Pricing Source, Collection Workflow, and Deployment Surface Audit

**Date:** 2026-07-06
**Run slug:** traderie-pricing-source-deployment-audit
**Scope:** All pricing sources, collectors, data flows, tracked/untracked/ignored files
**Status:** Read-only audit — no implementation authorized

---

## 1. Executive Answer

**Distinct pricing sites found:** 23

**With production-capable collectors:** 2 (Traderie API, ItemNow API)
**With prototype collectors:** 3 (D2Stock RSS, IGGM offline, MuleFactory offline)
**With partial/prototype collectors needing data:** 2 (G2G offline, Diablo2.io offline)
**Represented only by fixtures/manual captures:** 10 (Eldorado, MMOPixel, PlayerAuctions, Odealo, AOEAH, Chicks Gold, RPGStash, items7, eBay, YesGamers)
**Research only, no data:** 4 (Reddit, d2jsp, Discord Baal's Ledger, d2items_for_sale)
**Capable of unattended recurring runs today:** 1 — the Traderie API (cloudscraper, 4x daily via launchd, proven 355,794 JSONL records across 4 segments).

**Dataset composition:** Predominantly **live, historical Traderie completed-trade observations** (355,794 JSONL lines, 7,117 modeled trades in product, 7117-modeled-trade VWAP product). Cash data is 328 observations across 6 sources collected manually as one-shot browser captures — not recurring, not automated.

**Strong Codex should proceed with PostgreSQL.** The in-game trade pipeline (Traderie API) produces production-quality data that justifies database persistence. Cash sources are too thin and manual to justify PG by themselves, but they are `use_in_model=false` comparison data and will simply be additional tables. The core trade data (355K+ observations across 4 segments, growing ~2-5K per snapshot) is a proper relational workload.

---

## 2. Source Inventory

### A. In-Game Trade Sources

#### 1. Traderie API (canonical production source)

| Field | Value |
|---|---|
| Domain | `traderie.com` |
| Source ID | `traderie` |
| Segments | pc_sc_nl, pc_sc_l, pc_hc_l, pc_hc_nl |
| Price type | Completed player trades |
| Currency | Ist-normalized in-game (no cash) |
| Timestamps | `updated_at` per listing |
| Seller identity | Username + rating + reviews + score |
| Quantity | Yes (`amount` field) |
| Endpoint | `https://traderie.com/api/diablo2resurrected/listings` |
| Access | `cloudscraper` (Cloudflare bypass), no credentials |
| Legal | Unofficial API surface, not a public data product |
| Status | **Production** — 4x daily, launchd, exit 0 |
| Evidence | `data/history/traderie/*/completed_trades_*.jsonl` (355,794 lines) |

#### 2. Diablo2.io (candidate, not integrated)

| Field | Value |
|---|---|
| Domain | `diablo2.io` |
| Source ID | `diablo2_io` |
| Segments | PC SC L/NL, HC L/NL (filters confirmed) |
| Price type | Sold/completed trade posts (forum-style) |
| Currency | In-game rune trades |
| Access | Static HTML (no auth, no Cloudflare) |
| Status | **Prototype/Research** — offline parser against 4 saved fixtures; `use_in_model=false` |
| Evidence | `data/research/diablo2io_sold_rune_trades.sample.json` (14 candidate rows) |
| Known issue | Parser not validated; rows may not be reliable completed trades |

### B. Cash Market Sources

#### 3. D2Stock

| Field | Value |
|---|---|
| Domain | `d2stock.com` |
| Source ID | `d2stock` |
| Segments | Softcore Ladder/Non-Ladder (from RSS feed titles), no HC observed |
| Price type | Asking prices |
| Currency | USD |
| Prices | Per-unit asking |
| Access | Google Shopping RSS feed at `/rss.xml`, no auth, no browser |
| Status | **Prototype** — offline parser exists, snapshot_io integration not complete |
| Collected | 199 observations, one-shot fetch |
| Evidence | `data/external/d2stock_cash_prices.json`, `research/sources/captures/d2stock/` |

#### 4. IGGM

| Field | Value |
|---|---|
| Domain | `iggm.com` |
| Source ID | `iggm` |
| Segments | PC Non-Ladder Softcore ROTW (confirmed, high confidence) |
| Price type | Asking prices |
| Currency | USD |
| Status | **Prototype** — offline parser exists for saved browser capture |
| Collected | 30 observations, one-shot Camoufox capture + offline parse |
| Access | Requires browser (rendered HTML). Prices embedded in JSON inside rendered page |
| Evidence | `data/external/iggm_cash_prices.json`, `research/sources/captures/iggm_2026-06-20_runes-focused/` |

#### 5. ItemNow

| Field | Value |
|---|---|
| Domain | `itemnow.com` |
| Source ID | `itemnow` |
| Segments | PC Ladder SC/HC |
| Price type | Asking prices (WooCommerce product prices) |
| Currency | USD cents (converted to dollars) |
| Status | **Prototype** — live API fetcher exists, no auth needed |
| Collected | 42 observations, live API fetch + offline fixtures |
| Access | Public WooCommerce Store API `wp-json/wc/store/v1/products?category=99` |
| Evidence | `data/external/itemnow_cash_prices.json`, live URL works |

#### 6. MuleFactory

| Field | Value |
|---|---|
| Domain | `mulefactory.com` |
| Source ID | `mulefactory` |
| Segments | Unknown default (JS server selector) |
| Price type | "From" (minimum/base) prices |
| Currency | USD |
| Status | **Prototype** — static HTML microdata parser exists |
| Collected | 24 rune prices, one-shot static HTML download + offline parse |
| Access | Static HTML with Schema.org microdata, no auth |
| Evidence | `data/external/mulefactory_cash_prices.json`, `research/sources/downloads/` |

#### 7. G2G

| Field | Value |
|---|---|
| Domain | `g2g.com` |
| Source ID | `g2g` |
| Segments | Partial — embedded in listing titles (LoD vs ROTW ambiguous) |
| Price type | Asking prices |
| Currency | USD |
| Status | **Prototype** — offline parser exists for saved browser captures |
| Collected | 33 observations, one-shot Camoufox capture |
| Access | Requires browser (Vue.js SPA). Offer detail pages cause Camoufox JS errors |
| Evidence | `data/external/g2g_cash_prices.json`, `research/sources/captures/g2g_*/` |
| Known issue | LoD/ROTW taxonomy ambiguous; all listings show "LoD" even from D2R category |

#### 8. items7

| Field | Value |
|---|---|
| Domain | `items7.com` |
| Source ID | `items7` |
| Status | **Fixture only** — 0 parseable rows |
| Access | Static HTML does not contain prices; client-side rendered |
| Evidence | `data/external/items7_cash_prices.json` (empty), `research/sources/downloads/items7.html` |

#### 9-19. Remaining Cash Sources (all non-functional for automation)

| Source | ID | Status | Block Reason |
|--------|----|--------|-------------|
| Eldorado.gg | `eldorado` | Captured browser | Angular SPA, no embedded JSON, no parser |
| MMOPixel | `mmopixel` | Captured browser | JS anti-bot, Camoufox works but no rune-specific URL |
| PlayerAuctions | `playerauctions` | Captured browser | No sold/completed surface; Cloudflare blocks curl |
| Odealo | `odealo` | Captured browser | React app, per-item prices render after hydration |
| AOEAH | `aoeah` | Captured static | Prices in CSS-styled elements, not plain-text |
| Chicks Gold | `chicksgold` | Captured static | Fully dynamic, 6KB shell, minimal segment info |
| RPGStash | `rpgstash` | Discovered | Cloudflare + JS render; Camoufox crashes |
| eBay | `ebay` | Deferred | Anti-bot blocks curl and Camoufox |
| YesGamers | `yesgamers` | Deferred | Login wall |
| d2jsp | `d2jsp` | Deferred | Fully gated (login + Cloudflare) |
| Discord Baal's Ledger | `discord_baals_ledger` | Discovered | Not investigated |

#### 20. Reddit (community signal, not pricing)

| Field | Value |
|---|---|
| Source ID | `reddit` |
| Status | Deferred — qualitative only, not pricing |
| Evidence | 2,998 posts collected previously, 0 comment trees |

---

## 3. Collector/Workflow Inventory

### Production Workflows (unattended repeatable)

| Workflow | Script | Source | Schedule | Last Run | Live? | Deterministic? | Idempotent? |
|---|---|---|---|---|---|---|---|
| Traderie snapshot | `snapshot_traderie.py` via `run_traderie_snapshot_launchd.sh` | Traderie API | 05,11,17,23 daily | 2026-07-04T03:16 | Yes (cloudscraper) | Yes (same params → same 50-cap window) | Idempotent per observation_key (JSONL dedup) |
| Product regeneration | `regenerate_products.sh` (7-script pipeline) | JSONL history | 06:00 daily | 2026-07-03T10:00 | No (local only) | Yes | Yes |

### Semi-Automated Workflows (manually initiated, otherwise automated)

| Workflow | Script | Source | Live? | Comments |
|---|---|---|---|---|
| ItemNow fetch | `parse_itemnow_api.py` | ItemNow API | Yes (optional offline) | No auth, public WooCommerce API. Could be schedule-ified |
| D2Stock fetch | `parse_d2stock_rss.py` | D2Stock RSS | Yes (optional offline) | No auth, public RSS feed. Could be schedule-ified |

### One-Shot Browser Capture + Offline Parse Workflows

| Workflow | Capture Script | Parse Script | Source | Browser | Last Captured |
|---|---|---|---|---|---|
| IGGM | `capture_iggm_rune_focused.py` | `parse_iggm_offline.py` | IGGM | Camoufox | 2026-06-20 |
| G2G | `capture_g2g_preview.py` | `parse_g2g_cash_prices.py` | G2G | Camoufox | 2026-06-20 |
| MuleFactory | Manual download | `parse_mulefactory.py` | MuleFactory | Static (no browser) | 2026-06-20 |
| Diablo2.io | `capture_diablo2io_fixtures.py` (Playwright) | `parse_diablo2io_sold_search_offline.py` | diablo2.io | Playwright Chromium | 2026-06-20 |
| items7 | Manual download | `parse_items7_offline.py` | items7 | Static | 2026-06-20 |

### One-Shot Browser Captures with No Parser

| Workflow | Script | Source | Status |
|---|---|---|---|
| Eldorado smoke | `capture_source_smoke.py` | Eldorado.gg | Captured, not parsed |
| MMOPixel smoke | `capture_source_smoke.py` | MMOPixel | Captured, not parsed |
| PlayerAuctions smoke | `capture_source_smoke.py` | PlayerAuctions | Captured, not parsed |
| Odealo smoke | `capture_source_smoke.py` | Odealo | Captured, not parsed |
| YesGamers smoke | `capture_source_smoke.py` | YesGamers | Captured, not parsed |

### Research/Audit Workflows (one-shot, read-only)

| Workflow | Script | Purpose |
|---|---|---|
| Traderie pagination audit | `audit_traderie_pagination.py` | Investigated nextPage cursor behavior |
| Traderie raw fetch audit | `audit_traderie_raw_fetch.py` | Examined raw API response structure |
| Cash vs trade audit | `audit_cash_vs_trade_value.py` | Comparison report (no network) |
| Rune pair audit | `audit_rune_pairs.py` | Non-Ist trade analysis (no network) |
| Game version audit | `audit_traderie_game_version.py` | Ruleset distribution (no network) |

### Infrastructure/Auxiliary Workflows (no network, support only)

| Script | Purpose | Status |
|---|---|---|
| `build_traderie_dataset_from_history.py` | JSONL → extracted CSV | Production (in regen pipeline) |
| `calculate_rune_prices.py` | VWAP calculation | Production (in regen pipeline) |
| `generate_prices_json.py` | Product JSON generation | Production (in regen pipeline) |
| `generate_external_cash_prices.py` | Cash product merge | Production (in regen pipeline) |
| `collection_status.py` | Health report | Production (in regen pipeline) |
| `validate_*.py` (4 scripts) | Validation suite | Production (in regen pipeline) |
| `traderie_storage_adapter.py` | File adapter (abstracted I/O) | Implemented, tested |
| `traderie_pg_adapter.py` | **IN-MEMORY DRY STORE** | Implemented, not connected |
| `traderie_pilot_loader.py` | Pilot loader | Implemented, tested, blocked |
| `traderie_pilot_readiness_report.py` | Pilot readiness | Implemented, tested |
| `traderie_health_export.py` | Health JSON export | Inert/dry-run |
| `traderie_disk_inventory.py` | Disk inventory | Implemented |
| `traderie_parity_report.py` | File/PG parity | Implemented |
| `collection_status.py` | Snapshot health report | Production |

---

## 4. Data Provenance Trace (End to End)

### In-Game Trade Values (production, live)

```
Product: data/products/in_game_rune_values.json (7,117 modeled trades, 4 segments)
  ↑ generate_prices_json.py — reads rune_prices_{seg}.csv
  ↑ calculate_rune_prices.py — Ist-normalized VWAP
    ↑ build_traderie_dataset_from_history.py — reads JSONL → extracted CSV
      ↑ data/history/traderie/{seg}/completed_trades_{seg}.jsonl (355,794 lines)
        ↑ snapshot_traderie.py — append_history() via snapshot_io
          ↑ data/snapshots/normalized/traderie/{seg}/{ts}.json
          ↑ data/snapshots/raw/traderie/{seg}/{ts}/response.json (2.2 GB total)
            ↑ cloudscraper GET to https://traderie.com/api/diablo2resurrected/listings
              ↑ Traderie website user-to-user trade listings (rolling 50-cap)
```

Record example: `pc_sc_l` segment, "Jah Rune", listing_id `123456`, captured_at `2026-07-04T03:16:08Z`, updated_at `2026-06-28T14:22:00Z`, seller `player123`, price `[{name: "Ber Rune", quantity: 1}, {name: "Ist Rune", quantity: 3}]`.

### External Cash Prices (manual, one-shot)

```
Product: data/products/external_cash_prices.sample.json (328 obs, 6 sources)
  ↑ generate_external_cash_prices.py — merges per-source JSONs
    ├── data/external/iggm_cash_prices.json (30 obs)
    │     ↑ parse_iggm_offline.py — reads browser-captured page.html
    │       ↑ capture_iggm_rune_focused.py (Camoufox, 2026-06-20)
    │         ↑ https://www.iggm.com/d2-resurrected-items
    ├── data/external/itemnow_cash_prices.json (42 obs)
    │     ↑ parse_itemnow_api.py — live GET to WooCommerce API
    │         ↑ https://itemnow.com/wp-json/wc/store/v1/products?category=99
    ├── data/external/d2stock_cash_prices.json (199 obs)
    │     ↑ parse_d2stock_rss.py — reads RSS feed
    │         ↑ https://d2stock.com/rss.xml (live) OR saved fixture
    ├── data/external/g2g_cash_prices.json (33 obs)
    │     ↑ parse_g2g_cash_prices.py — reads browser-captured pages
    │       ↑ capture_g2g_preview.py (Camoufox, 2026-06-20)
    │         ↑ https://www.g2g.com/categories/diablo-2-resurrected-item-for-sale
    ├── data/external/mulefactory_cash_prices.json (24 obs)
    │     ↑ parse_mulefactory.py — reads static HTML fixture
    │         ↑ research/sources/downloads/rune_sources_2026-06-20/mulefactory.html
    └── data/external/items7_cash_prices.json (0 obs, empty)
          ↑ parse_items7_offline.py — reads static HTML (no prices extractable)
```

---

## 5. GitHub and VPS Deployment Surface

### A. Required in GitHub and VPS

| Path | Purpose | Workflow Stage | Runtime-Critical? | Portable? | Currently Tracked? | Cleanup Needed? |
|------|---------|---------------|-------------------|-----------|-------------------|-----------------|
| `scripts/snapshot_traderie.py` | Primary collector | Fetch | Yes | Yes (env vars for paths) | Yes | No |
| `scripts/lib/snapshot_io.py` | Snapshot/history I/O | Fetch → Store | Yes | Yes | Yes | No |
| `scripts/build_traderie_dataset_from_history.py` | History → extracted CSV | Process | Yes | Yes | Yes | No |
| `scripts/calculate_rune_prices.py` | VWAP pricing | Process | Yes | Yes | Yes | No |
| `scripts/generate_prices_json.py` | Product generation | Process | Yes | Yes | Yes | No |
| `scripts/generate_external_cash_prices.py` | Cash product merge | Process | Yes | Yes | Yes | No |
| `scripts/validate_in_game_rune_values.py` | Validation | Validate | Yes | Yes | Yes | No |
| `scripts/validate_external_cash_prices.py` | Validation | Validate | Yes | Yes | Yes | No |
| `scripts/collection_status.py` | Health report | Monitor | Yes | Yes | Yes | No |
| `scripts/validate_source_manifest.py` | Manifest validation | Validate | Advisory | Yes | Yes | No |
| `server_configs.json` | Segment definitions | All | Yes | Yes | Yes | No |
| `data/item_ids.json` | Item ID registry | Fetch | Yes | Yes | Yes | No |
| `data/rune_registry.json` | Rune catalog | Process/Product | Yes | Yes | Yes | No |
| `data/source_manifest.json` | Source ledger | All | Advisory | Yes | Yes | No |
| `requirements.txt` | Python dependencies | Setup | Yes | Yes | Yes | No |
| `.env.example` | Env var template | Setup | Yes | Yes | Yes | No |
| `db/migrations/*.sql` | Schema definitions | PostgreSQL | Yes (on VPS PG) | Yes | Yes | No |
| `db/validation/999_full_validation.sql` | Full validation | Validate | Yes | Yes | Yes | No |
| `db/fixtures/seed.sql` | Reference data | Setup | Yes | Yes | Yes | No |
| `scripts/run_traderie_snapshot_launchd.sh` | Launchd wrapper | Fetch | Yes (Mac) | Partially (Mac paths) | Yes | Already parameterized |
| `scripts/regenerate_products.sh` | Regen pipeline | Process | Yes | Yes | Yes | Already parameterized |

### B. Required in GitHub but not VPS runtime state

These files are needed in the GitHub repo for development, CI, and review but should NOT be copied to VPS as active runtime state:

| Path | Purpose | Why not on VPS |
|------|---------|----------------|
| `tests/` | Unit tests | VPS runs production, not tests |
| `.github/workflows/ci.yml` | CI | GitHub-only; VPS has no GitHub Actions runner |
| `.github/workflows/deploy.yml` | GH Pages deploy | GitHub-only |
| `tests/fixtures/` | Test fixtures | Large, not needed for production |
| `db/migrations/rollback/*.sql` | Rollback safety | Only needed during migration execution |
| `db/migrations/validation/*.sql` | Migration validation | Only needed during migration execution |
| `docs/` | Development docs | VPS should not need docs to run |
| `web/` source | Frontend source | VPS only needs built dist/ (or GH Pages serves it) |
| `prompts/` | Codex planning prompts | Development/planning only |
| `research/memos/` | Research notes | Development only |
| `notebook/` | Jupyter notebooks | Development only |

**VPS checkout approach:** The VPS will clone the full repo but only use `scripts/`, `data/`, `db/`, `server_configs.json`, `requirements.txt`, and `.env`. Tests, docs, web source, notebooks, and research can exist on disk without harm but are not invoked.

### C. Local/Runtime Only (must NEVER be tracked)

| Path/Pattern | Why Untracked | Retention | Mac Archive? |
|---|---|---|---|
| `data/history/` (410 MB) | Mutable production data, large | Keep as file authority until PG parity proven | Yes — archive after PG cutover |
| `data/snapshots/` (1.8 GB) | Mutable raw captures, very large | 30-day retention, can be regenerated | Optional |
| `data/research/` (62 MB) | Generated intermediates | Ephemeral | No |
| `data/prices/*.csv` | Generated intermediates | Ephemeral | No |
| `data/extracted/` | Generated intermediates | Ephemeral | No |
| `data/normalized/` | Generated intermediates | Ephemeral | No |
| `data/raw/` | Raw extracts | Ephemeral | No |
| `data/fetch_log.txt` | Runtime log | Ephemeral | No |
| `logs/` | Launchd service logs | 30-day | No |
| `.run/` | Lock files | Ephemeral | No |
| `web/dist/` | Built frontend | Generated by deploy_web.sh | No |
| `web/node_modules/` | Dependencies | Recreatable | No |
| `.venv/` | Python venv | Recreatable | No |
| `research/reddit/raw/` | Raw Reddit captures | Research only | Optional |
| `research/sources/captures/` (browser captures) | Browser artifacts, may contain cookies/secrets | Retain for audit; NOT for VPS | Yes — archive on Mac |
| `*.har`, `*.har/` | Browser HAR files | May contain credentials | No |
| `tools/subreddit_research/.env` | Reddit API credentials | Secret | No |
| `data/research/` | Research outputs | Stale after audit | No |

### D. Research/Archive Candidates

These files are tracked but should be considered for archiving or removal:

| Path | Classification | Recommendation |
|------|---------------|----------------|
| `dev/` directory (~50 MB tracked files, Traderie page downloads with ad/tracker scripts) | Stale experiment | **Archive** — contains 200+ files of downloaded Traderie page assets (ad scripts, tracking pixels, CSS, fonts). Not needed for production. Move to `_archive/dev/` or remove. |
| `scripts/old/` (52 legacy scripts) | Superseded | **Consolidate** — keep in `_archive/scripts/` for reference, remove from active root |
| `scripts/old/extracted/*.csv` | Generated legacy prices | **Remove** — old generated artifacts, recreatable |
| `notebook/*.ipynb` (6 notebooks) | Exploratory research | **Keep** in `_archive/notebooks/` |
| `research/memos/*.md` (42 memos from 2026-06-20) | Historical research | **Consolidate** — most are one-shot discovery. Keep a curated subset, archive the rest |
| `research/sources/captures/*/` (.html, .png, screenshots) | Historical captures | **Archive** — valuable for source audit but should not be in git |
| `research/sources/downloads/*.html` (11 downloaded pages) | One-shot discovery | **Archive** |
| `reports/*` (generated HTML reports) | Stale generated reports | **Remove** — regeneratable |
| `data/completed_pc_sc_nl_normalized.csv` | Legacy normalized data | Likely stale — verify then archive |
| `data/g2g_rune_prices_softcore_nonladder_pc.csv` | Legacy G2G export | Likely stale — verify then archive |
| `prompts/codex_graph_pricing_model.md` | Old Codex prompt | **Archive** — superseded by newer prompts |
| `prompts/codex_traderie_ship_plan.md` | Old Codex prompt | **Archive** |
| `tools/subreddit_research/` | Separate subsystem | Keep but document as non-core; not needed for VPS |
| `app-icons.py`, `app.py` | Legacy app | **Archive** — not part of current pipeline |
| `pages/trade_count.py` | One-off script | **Archive** |
| `research/item_candidates/` | Exploratory | **Archive** |
| `research/reddit/notes/` | Reddit research notes | **Archive** |
| `reports/*.py` | Report generation scripts | **Consolidate** — move to `scripts/old/` or `_archive/` |
| `data/traderie_catalogue.json` (195 KB) | Full Traderie item catalog | Keep — referenced by pipeline? Verify. If unused, archive. |
| `data/research/diablo2io_sold_*.sample.json` | Diablo2.io research samples | Keep but mark `use_in_model=false` (already is) |
| `data/research/memos/2026-06-20-traderie-raw-response-audit.md` | One-shot memo | Move to `research/memos/` or archive |
| `docs/TRADERIE_COMPLETED_TRADES_AUDIT.md` | Historical audit | Keep for reference |
| `docs/TRADERIE_NORMALIZED_SCHEMA.md` | Historical schema doc | Likely superseded by db/migrations/ |
| `docs/TRADERIE_OVERLAY_PATCH_PLAN.md` | Old patch plan | Archive |
| `docs/TRADERIE_TOOLS_INTEGRATION.md` | Old integration doc | Keep for userscript reference |
| `docs/USERSCRIPT.md` | Userscript documentation | Keep for userscript reference |
| `docs/CODEX_HANDOFF.md` | Stale handoff doc | Archive |
| `docs/ivy_manifest.json`, `docs/ivy_manifest.meta.json` | Ivy-control manifest | Likely not needed here — check if ivy-control owns this |

### E. Missing Tracked Assets

| Required Asset | Status | Issue |
|---|---|---|
| `README.md` (public-facing) | **MISSING** | Only `README_INTERNAL.md` exists. Public README needed for GitHub push. |
| `LICENSE` | **MISSING** | No license file. MIT recommended. |
| `scripts/deploy/systemd/*` wrapper scripts for VPS | **TRACKED BUT INERT** | `deploy/systemd/*.service` files reference scripts that don't exist as VPS variants |
| VPS variant of `run_traderie_snapshot_launchd.sh` | **MISSING** | Current script uses Mac paths and `launchd`-style lock |
| VPS variant of `regenerate_products.sh` | **PARTIALLY MISSING** | Parameterized for env vars but not adapted for VPS filesystem |
| VPS `.env` file template | **MISSING** | `deploy/env.example` exists but is separate from `.env.example` |
| `scripts/run_traderie_backup.sh` | **MISSING** | Referenced by `deploy/systemd/traderie-backup-postgres.service` |
| `scripts/run_traderie_validate.sh` | **MISSING** | Referenced by `deploy/systemd/traderie-validate-products.service` |
| `scripts/run_traderie_snapshot.sh` (VPS variant) | **MISSING** | Referenced by `deploy/systemd/traderie-ingest-snapshot.service` |
| `scripts/run_traderie_retain.sh` | **MISSING** | Referenced by `deploy/systemd/traderie-retain-snapshots.service` |

### F. Fresh-Clone Proof

A fresh GitHub clone should be able to:

1. **Create environment:** `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` — ✅ `requirements.txt` exists with `cloudscraper`, `numpy`, `pandas`
2. **Install dependencies:** Same as above — ✅
3. **Connect to PostgreSQL:** Requires `TRADERIE_PG_URL` or individual env vars. `.env.example` documents the variables. PostgreSQL adapter is disabled by default. — ✅ documented, ❌ no live adapter yet
4. **Apply/verify migrations:** `psql -d traderie -f db/migrations/20260705_*.sql` — ✅ migrations exist with rollbacks and validation
5. **Fetch one bounded source sample:** `python3 scripts/snapshot_traderie.py --segment pc_sc_l --single` — ✅ live fetch works (cloudscraper), produces raw + normalized snapshots and appends to JSONL history
6. **Process it:** `python3 scripts/build_traderie_dataset_from_history.py && python3 scripts/calculate_rune_prices.py` — ✅ produces priced CSV
7. **Persist it:** Currently JSONL-based. PG persistence requires real adapter. — ⚠️ JSONL works, PG blocked
8. **Validate it:** `python3 scripts/validate_in_game_rune_values.py && python3 scripts/validate_external_cash_prices.py` — ✅
9. **Export health:** `python3 scripts/collection_status.py` — ✅
10. **Run tests:** `python3 -m pytest tests/` — ✅ 46/46 pass

**Gap:** The PostgreSQL adapter is in-memory only. A fresh clone cannot persist to PostgreSQL without implementing the real adapter.

### G. Recommended Curated Repository Shape

| Current Top-Level Path | Classification | Recommendation |
|---|---|---|
| `scripts/` | **Keep** — core pipeline | Remove `scripts/old/` to `_archive/scripts/` |
| `scripts/lib/` | **Keep** — core library | No change |
| `data/` | **Keep** — tracked products and registries | Remove stale CSVs (completed_pc_sc_nl_normalized.csv, g2g_rune_prices*.csv) to archive |
| `db/` | **Keep** — migrations and schema | No change |
| `deploy/` | **Keep** — future VPS deployment config | Mark as INERT; wrapper scripts still need creation |
| `web/` | **Keep** — frontend | Required for GH Pages deploy |
| `tests/` | **Keep** — test suite | No change |
| `docs/` | **Consolidate** | Archive stale docs (CODEX_HANDOFF, OLD patch plans). Keep: ARCHITECTURE, PRICING_MODEL, DATA_PRODUCTS, SOURCE_MANIFEST, VPS_CONTINUITY, backup-restore, retention, LAUNCHD_SETUP, USERSCRIPT |
| `launchd/` | **Keep** — Mac scheduling | Needed while Mac is primary. Template for VPS systemd conversion |
| `AGENTS.md` | **Keep** | Agent routing contract |
| `ROADMAP.md` | **Keep** | Product roadmap |
| `VPS_ROADMAP.md` | **Keep** | Infrastructure companion roadmap |
| `SESSION.md` | **Keep** | Current session state |
| `LOG.md` | **Keep** | Activity log |
| `BACKLOG.md` | **Keep** | Post-alpha backlog |
| `README_INTERNAL.md` | **Keep** | Internal state doc |
| `.env.example` | **Keep** | Environment template |
| `requirements.txt` | **Keep** | Dependencies |
| `server_configs.json` | **Keep** | Segment definitions |
| `.github/` | **Keep** | CI/CD workflows |
| `prompts/` | **Consolidate** | Archive old prompts (graph_pricing, ship_plan). Keep current (codex_vps_postgres_roadmap) |
| `research/memos/` | **Consolidate** | Archive to `_archive/research/` |
| `research/sources/` | **Archive** | Captures and downloads should be untracked, not in git |
| `research/reddit/` | **Archive** | Reddit research data should be untracked |
| `research/item_candidates/` | **Archive** | Exploratory |
| `dev/` | **Remove from tracking** | 50 MB of ad/tracker page downloads. Should not be in git |
| `notebook/` | **Archive** | Move to `_archive/notebooks/` |
| `reports/` | **Remove** | Generated artifacts, not source |
| `tools/` | **Keep** but separate | `tools/subreddit_research/` is a distinct subsystem |
| `icons/` | **Keep** | Web app icons |
| `_outbox/` | **Keep** (gitignored) | Planning packet output directory |
| `.agent-workflow/` | **Ignore** | Already gitignored; agent runtime state |

**Recommended new files to add:**
- `README.md` (public-facing)
- `LICENSE` (MIT)
- `deploy/systemd/traderie-ingest-snapshot.wrapper.sh` (VPS wrapper script)
- `scripts/run_traderie_snapshot.sh` (VPS variant of launchd wrapper)
- `scripts/run_traderie_backup.sh` (referenced by systemd unit)
- `scripts/run_traderie_validate.sh` (referenced by systemd unit)

### H. Strong Codex Implications

**Files Strong Codex should modify:**
1. `scripts/traderie_pg_adapter.py` — Replace in-memory dry store with real PostgreSQL connection using `traderie_writer`
2. `scripts/traderie_health_export.py` — Move from inert/dry-run to production readiness
3. `scripts/snapshot_traderie.py` — Add optional PG dual-write after adapter is real
4. `scripts/lib/snapshot_io.py` — Add optional PG persistence alongside JSONL

**Cleanup Strong Codex may perform (mechanical, no data risk):**
1. Remove `dev/` from tracking (`git rm -r dev/`)
2. Move `scripts/old/` to `_archive/scripts/`
3. Add `README.md` and `LICENSE`
4. Create missing VPS wrapper scripts (inert, not activated)
5. Update `.gitignore` for remaining capture/research paths
6. Consolidate stale docs

**Cleanup that requires Buddy review:**
1. `research/sources/captures/*/` — contains browser captures with screenshots; may be sensitive
2. `dev/Traderie_page_files/` — contains ad/tracker content; confirming it's safe to delete
3. Removing `data/traderie_catalogue.json` — verify it's unused
4. Removing `data/completed_pc_sc_nl_normalized.csv` and `data/g2g_rune_prices*` — verify stale
5. License choice (MIT vs other)

**Files that must NOT be deleted:**
- `data/source_manifest.json` — canonical source registry
- `data/rune_registry.json` — canonical rune catalog
- `data/item_ids.json` — lookup for Traderie API
- `data/products/*.json` — current published products
- `server_configs.json` — segment definitions
- Any `scripts/` file actively referenced by the pipeline
- `db/migrations/*.sql` — schema authority

**Curation timing:** Curation should happen **before** the Strong Codex PostgreSQL adapter work. A clean repo reduces confusion, eliminates stale references, and ensures the adapter work targets only the correct files.

---

## 6. Final Verdicts

### Is the current repository suitable for a public or private GitHub push?

**Private GitHub push: ✅ Ready (with caveats)**
- 46/46 tests pass
- CI workflow configured
- `.gitignore` covers large generated paths
- No secrets in tracked files
- No `.db` files tracked
- Hardcoded `/Users/buddy/` paths in shell scripts already parameterized
- Launchd plists still use absolute paths (required by launchd on Mac — acceptable)

**Blocker for push:** Missing `README.md` and `LICENSE`. The `dev/` directory (50 MB of ad/tracker assets) should be removed from tracking first.

### Is it suitable for a VPS checkout?

**VPS checkout: ⚠️ Ready for code, not for operation.**
- The code can be cloned and will run if Python deps are installed
- VPS wrapper scripts for systemd are missing (pointed at by unit files but not created)
- PostgreSQL adapter is in-memory only — no data will persist
- `cloudscraper` on Ubuntu 24.04 is untested (Likely works but not validated)
- The VPS checkout will work for: testing, manual fetch runs, dry-run validation

### Can a fresh clone run the full pipeline?

**Fetch + process + validate: ✅ Yes**
- `snapshot_traderie.py` works from any clone (cloudscraper + env vars)
- `regenerate_products.sh` works from any clone (reads local files, writes local files)
- Validation works from any clone

**Persist to PostgreSQL: ❌ No**
- Adapter is in-memory dry store
- No real adapter to connect to `traderie` database

**Deploy web dashboard: ❌ No**
- No GitHub remote configured
- GH Pages deploy workflow exists but cannot trigger

### Minimum Operational File Set

```
scripts/
  snapshot_traderie.py, lib/snapshot_io.py
  build_traderie_dataset_from_history.py
  calculate_rune_prices.py
  generate_prices_json.py, generate_external_cash_prices.py
  collection_status.py
  validate_*.py (4 files)
  run_traderie_snapshot_launchd.sh (Mac) OR _snapshot.sh (VPS variant)
  regenerate_products.sh
data/
  item_ids.json, rune_registry.json, source_manifest.json
  server_configs.json
  products/ (output)
db/
  migrations/*.sql, validation/999_full_validation.sql
requirements.txt
.env.example
```

That is approximately 15-20 files. Everything else is support, development, or archival.

### What must be cleaned before the Strong Codex session?

| Priority | Item | Why |
|----------|------|-----|
| **P0** | Remove `dev/` from tracking (~50 MB ad/tracker files) | Should not be in git; cleanup before push |
| **P0** | Add `README.md` and `LICENSE` | Required for GitHub push; Codex will expect them |
| **P1** | Move `scripts/old/` to `_archive/scripts/` | Reduces confusion about which scripts are active |
| **P1** | Consolidate `research/memos/` (42 files) to `_archive/research/` | Production workflow shouldn't reference old discovery memos |
| **P2** | Create VPS wrapper scripts (inert, documented as such) | Systemd units reference them; silence the missing-file warnings |
| **P2** | Remove stale CSV data files from `data/` root | `completed_pc_sc_nl_normalized.csv`, `g2g_rune_prices_*` |
| **P3** | Update `.gitignore` for `research/sources/captures/` (currently NOT in gitignore!) | Browser captures should not be tracked |
| **P3** | Archive old docs: CODEX_HANDOFF, OLD patch plans, stale memos | Clean up docs/ for push readiness |
| **P3** | Remove `reports/` from tracking (generated HTML reports) | Not source code |

**Note:** `research/sources/captures/` is currently **tracked** in git (it appears in the tracked file list above). These are browser captures with screenshots, network logs, and listing samples. They should be moved out of git before public push.
