# D2R Market Helper — Repo State + Next Actions

Date: 2026-06-20
Repo: /Users/buddy/projects/traderie
Current HEAD: cdd55f9 (7 milestone commits after initial memory snapshot)
Launchd job installed: com.buddy.traderie.snapshot-traderie

---

## 1. Product Definition

D2R Market Helper is a multi-source market intelligence hub for Diablo II: Resurrected traders.

**Current honest thesis:** Traderie-normalized in-game rune values + multi-source external cash comparison + source transparency / caveats / discovery ledger.

**Multi-source completed-trade normalization is not claimed yet.** Diablo2.io is research-only (14 candidate rows, insufficient volume). The project's center of gravity remains Traderie as the canonical in-game source.

**Core rules:**
- In-game values and cash prices are always separate.
- Never blend cash-market prices into in-game rune ratios.
- Every displayed number must be visibly tied to segment, source, evidence class, and confidence/caveat.
- Economy segments (pc_sc_l, pc_sc_nl, pc_hc_l, pc_hc_nl) are never merged.

---

## 2. Current Data Tracks

### A. In-game barter pricing

- **Source:** Traderie only (rolling 50-cap recent completed-trade feed).
- **Products:** `data/products/in_game_rune_values.json` (4 segments, 92 rune observations, 2,570 modeled trades), `data/products/traderie_tools_prices.json` (userscript-compatible feed).
- **Window:** `source_window_label: rolling_recent_trades_50_cap`. Traderie `completed=true` returns at most 50 recent listings per item/segment. `nextPage` is boolean/repeating — not real pagination. High-volume items cycle ~7h; low-volume items retain listings for weeks to months.
- **VWAP model:** Ist-normalized bid/ask. AND trades excluded. Active listings excluded.
- **Retained audit fields:** `listing_id`, `seller.rating`, `seller.reviews`, `prices[].item_id`, `active`/`completed` bools, `version`, `nextPage`, explicit platform/ladder/hardcore segment metadata.
- **Known gaps:** No buyer field exposed by API. No `created_at`/`completed_at`. Only `updated_at`. History depends entirely on scheduled polling.

### B. External cash comparison

- **Sources/parsers:**
  - IGGM (`scripts/parse_iggm_offline.py`): 30 observations, tier_2, high segment confidence.
  - ItemNow (`scripts/parse_itemnow_api.py`): 42 observations, WooCommerce Store API, no auth.
  - D2Stock (`scripts/parse_d2stock_rss.py`): 199 observations, RSS/XML, 2 segments observed.
  - items7 (`scripts/parse_items7_offline.py`): 0 rows, deferred (client-side rendering).
- **Product:** `data/products/external_cash_prices.sample.json` — 271 observations across 4 sources, schema v0.2.
- **All rows:** `use_in_model=false`, `evidence_class=cash_listing`, `segment_confidence=low` unless proven.
- **Window:** `source_window_label: current_snapshot`. Cash sources are current-only; project history starts when snapshots begin.

### C. Source intelligence

- **Ledger:** `data/source_manifest.json` — 20 sources, all validated.
- **Discovery protocol:** 7-stage process now includes mandatory surface checks. Sources cannot be classified as qualitative/reference/cash-only until sold/completed/history surfaces are explicitly checked and recorded.
- **Status lifecycle:** discovered → captured_static / captured_browser → offline_parse_candidate → parser_prototype_ready → integrated. Also supports deferred/rejected.

### D. Snapshot/history layer

- **Infrastructure:** `scripts/lib/snapshot_io.py` — `write_raw_snapshot`, `write_normalized_snapshot`, `append_history`, `observation_key`, `content_hash`.
- **Paths (all gitignored):** `data/snapshots/raw/<source>/<ts>/`, `data/snapshots/normalized/<source>/<ts>.json`
- **History (gitignored):** `data/history/<source>/<dataset>.jsonl` — append-only, deduped by observation_key.
- **Adopted parsers:** ItemNow (3 runs, 84 history entries), Traderie snapshot collector.
- **Principle:** Raw and intermediate data stay private. Public products are generated from normalized/history sources.

### E. Static UI

- **Stack:** Vite 8 + React 19 + TypeScript + react-router-dom.
- **Pages:** `/` (market overview), `/runes` (full dashboard), `/sources` (directory), `/about-methodology`.
- **Segment selector:** URL query param `?segment=pc_sc_nl`. All 4 PC segments supported.
- **Cash separation:** In-game and cash columns visually distinct. Cash disclaimer on every page.
- **Diablo2.io status:** Labeled research-only / thin completed-trade reference signal — not integrated.
- **Build:** 0 tsc errors, production ~100KB gzip.

---

## 3. Source Status Table

| Source | Status | Priority | Role | Use in Model |
|---|---|---|---|---|
| **Traderie** | integrated | tier_1 | Canonical in-game completed-trade source (rolling 50-cap, 4x daily snapshots) | Primary |
| **IGGM** | parser_prototype_ready | tier_2 | Cash comparison (30 obs, high segment confidence) | false |
| **ItemNow** | parser_prototype_ready | tier_3 | Cash comparison (42 obs, WooCommerce Store API) | false |
| **D2Stock** | parser_prototype_ready | tier_3 | Cash comparison (199 obs, RSS/XML, 2 segments) | false |
| **Diablo2.io** | parser_prototype_ready | tier_1 (caveated) | Research: 14 candidate rows / 12 clean. Insufficient volume for modeling. | false |
| **MuleFactory** | captured_static | tier_3 | Cash parser candidate (24 runes, static microdata) | false |
| **Eldorado** | captured_browser | tier_3 | Cash parser candidate (476 listings, rendered) | false |
| **MMOPixel** | captured_browser | tier_3 | Cash parser candidate (1,304 items, rendered) | false |
| **PlayerAuctions** | captured_browser | tier_3 | Cash active listings only — no sold/completed surface. Deferred. | false |
| **G2G** | captured_browser | tier_2 | Cash marketplace, taxonomy unresolved (LoD vs ROTW). Deferred. | false |
| **items7** | captured_static | tier_3 | 0 parseable rows. Needs browser capture. | false |
| **YesGamers** | deferred | tier_3 | Login wall | false |
| **d2jsp** | deferred | later | Fully gated (Cloudflare + login). FG economy separate. | false |
| **Reddit** | deferred | tier_3 | Qualitative only | false |
| **Discord / Baal's Ledger** | discovered | later | Gated/manual downstream research only | false |
| **eBay** | discovered | later | Anti-bot blocks all automation | false |
| **RPGStash** | captured_static | later | Camoufox crashes; needs manual capture | false |
| All others | discovered | later | Zero artifacts, caveated unproven | false |

---

## 4. Traderie Pipeline State

### Endpoint
```
GET https://traderie.com/api/diablo2resurrected/listings
  completed=true
  auction=false
  prop_Platform=PC
  prop_Mode={softcore|hardcore}
  prop_Ladder={true|false}
  item={traderie_item_id}
```

### Pipeline
- `scripts/fetch_completed_trades.py` — iterates segments × categories × items via cloudscraper.
- `scripts/snapshot_traderie.py` — same logic but writes timestamped snapshots + history JSONL.
- `scripts/extract_rune_trades.py` — filters rune-for-rune trades, writes CSV.
- `scripts/generate_prices_json.py` — reads CSVs, outputs Ist-normalized VWAP products.
- `scripts/audit_traderie_raw_fetch.py` — single-item raw response inspector.
- `scripts/audit_traderie_pagination.py` — pagination behavior tester.

### Known Traderie facts (audit-proven)
- `completed=true` returns at most 50 listings per item/segment (count-capped, not time-capped).
- `nextPage` is a boolean/repeating indicator (0 or 1), not a sequential page cursor. All "pages" return the same 50 listings.
- No buyer field is exposed in completed-trade responses.
- No `created_at` or `completed_at` timestamp. Only `updated_at` (ISO 8601).
- `seller.reviews` is the total trades count for that seller.
- Segment metadata is in the `properties[]` array per listing.
- No rate-limit headers observed in bounded test (10 sequential pages, all 200 OK).

### Current pipeline status
- All the above risks are now known and documented.
- History is accumulated via scheduled snapshots, not API pagination.
- AND trades are extracted but not yet modeled.
- Confidence rules: High (50+ trades), Medium (15-49), Low (1-14), Unavailable (0).

---

## 5. Launchd Operational State

- **Namespace:** `com.buddy.traderie.*`
- **Installed label:** `com.buddy.traderie.snapshot-traderie`
- **Schedule:** 05:00 / 11:00 / 17:00 / 23:00 (avoids existing 03:00–03:30 buddy jobs)
- **Installed plist:** `~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist`
- **Repo template:** `launchd/com.buddy.traderie.snapshot-traderie.plist`
- **Runner:** `scripts/run_traderie_snapshot_launchd.sh`
- **Lock:** `.run/locks/snapshot-traderie.lock` using `mkdir` atomic lock (macOS has no flock)
- **Logs:** `logs/launchd/snapshot-traderie.{out,err}.log`
- **Ignored runtime paths:** `data/snapshots/`, `data/history/`, `logs/`, `.run/`
- **State at close:** Loaded/idle. All 4 segment history files exist. pc_hc_nl timeout was persistent — fixed by 30s hardcore timeout + retry/backoff.
- **Safety:** No other launchd labels were touched. Future agents must not bootstrap/bootout/kickstart/unload/remove this job unless explicitly asked. Safe inspect command: `launchctl print gui/$(id -u)/com.buddy.traderie.snapshot-traderie`.

---

## 6. Key Technical Findings

1. **Traderie is a rolling 50-cap feed, not a historical API.** History must be built by scheduled polling.
2. **Diablo2.io sold-search volume is structurally too low for modeling.** Page 2 does not exist. 14 rows across 4 runes is insufficient.
3. **ItemNow WooCommerce Store API is the cleanest public endpoint** — no auth, 42 products, 9/10 parseability.
4. **D2Stock RSS feed is the largest cash source** — 199 observations, 2 segments with segment-specific prices.
5. **d2jsp is fully gated** — Cloudflare + login wall. FG economy cannot be evaluated without access.
6. **Cash sources are current-only.** Snapshotting is the only way to build cash price history.
7. **Snapshot/history infrastructure is working.** 4 Traderie segment histories, 84 ItemNow history entries accumulated.

---

## 7. Git State

Current commits (newest first):
```
cdd55f9 chore: add generation products and web project metadata
90c2a57 feat: add static market dashboard scaffold
83e1383 feat: harden Traderie rolling-feed collection
fe54f1a feat: add snapshot history infrastructure and launchd setup
9b48fda research: add Diablo2.io sold-trade parser fixtures
ee23b74 feat: add external cash price parsers and schema v0.2
6579232 docs: formalize D2R market source discovery
ce2eba0 docs: add project memory snapshot
013c994 init: D2R Market Helper — pricing pipeline, item registry, source discovery, external cash-price prototype
```

All commits staged individually (no `git add .`, `git add -A`, or `git commit -a`).
Working tree core files clean. Remaining untracked files are intentional scratch/probe artifacts (probe sample JSONs, browser screenshots, session scratch docs).

**Ignored runtime data:** `data/snapshots/`, `data/history/`, `logs/`, `.run/`, `data/raw/`, `data/extracted/`, `.venv/`, `web/dist/`, `web/node_modules/`, `*.har`.

---

## 8. Validation Status

Last full green smoke test: `research/memos/2026-06-20-integration-smoke-test.md`

| Check | Result |
|---|---|
| `validate_source_manifest.py` | ✅ 20 sources valid |
| `validate_external_cash_prices.py` | ✅ 271 obs, 4 sources, schema v0.2 |
| `validate_in_game_rune_values.py` | ✅ Both products |
| `parse_itemnow_api.py` | ✅ 42 products |
| `parse_d2stock_rss.py` | ✅ 199 obs |
| `generate_external_cash_prices.py` | ✅ 271 merged |
| `generate_prices_json.py` | ✅ 4 segments, 92 obs, 2,570 trades |
| `snapshot_traderie.py --segment pc_sc_nl --item "Jah Rune"` | ✅ 50 listings, 50 unique IDs |
| `web build` | ✅ 0 tsc errors, ~100KB gzip |
| `bash -n` runner script | ✅ Syntax OK |
| `plutil -lint` plist | ✅ Valid |

---

## 9. Product Files

| File | Status | Notes |
|---|---|---|
| `data/source_manifest.json` | ✅ Active | 20 sources, all validated |
| `data/products/in_game_rune_values.json` | ✅ Active | 4 segments, 92 obs, 2,570 trades |
| `data/products/traderie_tools_prices.json` | ✅ Active | Userscript-compatible |
| `data/products/external_cash_prices.sample.json` | ✅ Active | 271 obs, 4 sources, schema v0.2 |
| `data/rune_registry.json` | ✅ Active | 33 runes, id 1-33, crosswalk fields |
| `data/external/iggm_cash_prices.json` | ✅ Active | 30 IGGM observations |
| `data/external/itemnow_cash_prices.json` | ✅ Active | 42 ItemNow observations |
| `data/external/d2stock_cash_prices.json` | ✅ Active | 199 D2Stock observations |
| `data/external/items7_cash_prices.json` | ✅ Active | 0 observations (documented limitation) |

---

## 10. Next Actions

ROADMAP.md is the active task authority. Current priorities are: 1. Refresh stale docs and source manifest state. 2. Decide whether to model Traderie AND trades. 3. Add MuleFactory cash parser if data quality is approved. 4. Choose launchd regeneration strategy. 5. Decide pc_hc_nl skipped-item policy. 6. Run final validation and separate backlog.

---

## 11. Known Caveats

### Traderie
- Unofficial API — behavior may change without notice.
- Count-capped at 50 listings per item/segment — no historical backfill via API.
- No buyer field. No created_at/completed_at. Only updated_at.
- Rate limits not fully characterized.
- AND trades extracted but not modeled.
- Cloudscraper reliability in high-frequency polling unknown.
- Hardcore segment API responses are slower/unreliable (low trade volume). Script now uses 30s timeout with 2 retries (5s/15s backoff) for hardcore segments; softcore uses 10s.

### External cash
- All prices are asking prices, not completed sales.
- Source segments may not match Traderie segments.
- Prices may include seller margin, delivery risk, and site fees.
- D2Stock shows segment-specific pricing but segment filter URL behavior unverified.
- IGGM confirmed for PC / Non-Ladder / Softcore / ROTW only.

### Diablo2.io
- Sold-search surface produces 2-7 rows per rune. Page 2 does not exist.
- 14 total candidate rows (12 clean) — insufficient for model comparison.
- Parser_prototype_ready but not integrated. All rows use_in_model=false.
- Segment filter parsing from HTML is automated but not fully validated.

### General
- Multi-source completed-trade normalization is not yet viable.
- Hardcore segments (especially non-ladder) have very thin volume.
- Project history for all sources starts when scheduled snapshots began.
- d2jsp, Discord, eBay, RPGStash are gated/manual — no automation possible.

---

## 12. Completed-Trade Source Confidence Plan

### Current Confidence Statement

- **Confidence that Traderie is ready for canonical completed-trade modeling:** high.
- **Confidence that no other usable completed-trade/history surfaces exist:** low-to-moderate.
- **Target confidence:** medium-high after a dedicated completed-trade discovery pass.
- **Do not claim all sources have been found until the pass is complete.**

### Why Confidence Is Not Yet Medium-High

- Diablo2.io sold-search was missed during initial source evaluation and only found during a follow-up. The process was patched, but the patch has not been stress-tested across all sources.
- Many sources only had shallow probes — a homepage check and a single search, not a systematic completed/history search.
- Completed/history surfaces may hide behind:
  - Item-specific pages (not always linked from category pages)
  - Search/URL params not obvious from UI
  - JS-rendered filter toggles
  - Old archived forum pages
  - Gated communities (d2jsp, Discord)
- Cash storefronts were probed for current listings, but some marketplaces expose sold/history filters that may reveal completed-trade data.
- No broad web search for "D2R completed trades" or "D2R trade history trackers" has been performed.

### Mandatory Evidence Gates

Before claiming source coverage is medium-high, every candidate must have explicit evidence for:

1. **Completed/sold/history search terms tested** — source internal search or site search with terms like "sold", "completed", "closed", "archived", "WTS SOLD".
2. **Item-specific high-rune pages tested** — at least Jah and Ber tested per candidate source.
3. **Search/filter URL params inspected** — `?sold=1`, `?completed=true`, `?status=closed`, etc.
4. **Static/rendered/API access checked** — which access method works for the source.
5. **Pagination/window behavior checked** — where a completed/history surface exists.
6. **Artifact or memo proving the result** — even negative results must be recorded.
7. **Model eligibility decision recorded** — whether the surface is model-ready, diagnostic-only, research-only, or ineligible.

### Detailed Plan

See `research/memos/2026-06-20-completed-trade-source-confidence-plan.md` for the full discovery campaign definition, including:
- 18+ candidate sources to search
- 17 mandatory search terms
- 11 mandatory item probes
- Evidence scoring dimensions
- Confidence gates
- 3-batch campaign plan (public search, deep probes, artifact/manifest update)
