# Session Log: Market Pipeline Milestone

Date: 2026-06-20
Repo: /Users/buddy/projects/traderie
Initial state: 013c994 (init commit) + ce2eba0 (project memory) — 2 pre-existing commits
Milestone: 7 new commits (6579232 → cdd55f9)
Final state: 9 commits total, HEAD cdd55f9

---

## A. Executive Summary

### What the project became
D2R Market Helper — a multi-source market intelligence hub for Diablo II: Resurrected traders.
Traderie-based in-game rune value model + multi-source external cash comparison + full source discovery and transparency layer.

### Current honest thesis
**Traderie-normalized in-game rune values + multi-source external cash comparison + source transparency / caveats / discovery ledger.**

Multi-source completed-trade normalization is **not claimed yet**. Diablo2.io was investigated as the most promising second completed-trade candidate but found to have insufficient volume (14 candidate rows across 4 runes). The project's center of gravity remains Traderie as the canonical in-game source, with cash and discovery as supporting layers.

### Key architectural turn
Traderie's API was discovered to be a **rolling 50-cap recent-trades feed**, not a historical source. `completed=true` returns at most 50 listings per item/segment with no real pagination (`nextPage` is a boolean/repeating bit). This changed the pipeline from "fetch once and model" to "schedule snapshots and retain history via append-only JSONL."

---

## B. Timeline / Phases

### Phase 1: Process correction
- Discovered that Diablo2.io has an `activesold=1` sold-search surface that was missed during initial source evaluation.
- Workflow patched: mandatory source surface checklist added to `docs/SOURCE_MANIFEST.md`.
- Classification rule added: agents must explicitly search for sold/completed trade surfaces before classifying a source.

### Phase 2: Diablo2.io sold-search discovery
- Captured Jah sold-search fixture (7 candidate rows).
- Built offline parser (`scripts/parse_diablo2io_sold_search_offline.py`).
- Updated source manifest: `discovered` → `offline_parse_candidate` → `parser_prototype_ready`.

### Phase 3: Diablo2.io volume reality check
- Captured Ber, Lo, Sur sold-search fixtures (2-3 rows each).
- Total across all 4 runes: **14 candidate rows, 12 clean**.
- **None reach the 20-observation threshold** needed for model comparison.
- Conclusion: Diablo2.io sold-search is a thin reference signal, not a primary competitor to Traderie.
- The project thesis adjusted: no longer claiming multi-source completed-trade normalization.

### Phase 4: Broad source audit
- 20-source surface inventory audit: 8 of 20 sources had zero capture evidence.
- Formal 7-stage discovery protocol written.
- Candidate source expansion map created.
- Rankings repaired: IGGM raised (was below unparsed sources), PlayerAuctions/items7 lowered.

### Phase 5: Zero-artifact source probes
- Probed eBay, Eldorado, MMOPixel, MuleFactory, RPGStash, D2Stock.
- Found: D2Stock RSS feed (2,014 items, parseable), MuleFactory static microdata (24 runes), Eldorado rendered (476 items), MMOPixel rendered (1,304 items).
- RPGStash: Camoufox crashes (driver error). eBay: anti-bot blocks everything.
- Probed d2jsp: fully gated behind login+Cloudflare → deferred. Reddit: qualitative only.

### Phase 6: ItemNow cash parser
- Probed itemnow.com: found public WooCommerce Store API at `/wp-json/wc/store/v1/products`.
- No auth required. 42 products extracted (33 individual runes + 9 bundles).
- Built `scripts/parse_itemnow_api.py` with snapshot integration.
- All rows: `use_in_model=false`, `segment_confidence=low`, `evidence_class=cash_listing`.

### Phase 7: D2Stock RSS parser
- Built `scripts/parse_d2stock_rss.py` extracting from Google Shopping XML feed.
- 199 observations (66 rune singles + 133 bundles) across 2 segments.
- First segment-specific pricing observed: Ber $7.94 ladder vs $6.84 non-ladder.
- All rows: `use_in_model=false`.

### Phase 8: External cash schema v0.2
- Hardened `scripts/validate_external_cash_prices.py`: 11 required fields, rejects `use_in_model=true`, enforces `evidence_class=cash_listing`, validates `item_type` controlled vocabulary.
- Added `normalized_item_name`, `item_type`, `price_cents`, `product_url` fields.
- Cross-source naming crosswalk via `data/rune_registry.json`.
- External cash product now: **271 observations across 4 sources** (IGGM 30, ItemNow 42, items7 0, D2Stock 199).

### Phase 9: Traderie raw audit
- Fetched one Jah pc_sc_nl response with full field inspection.
- Found: no buyer field, no created_at/completed_at. Only updated_at and seller.
- Pipeline updated to retain: `listing_id`, `seller.rating`, `seller.reviews`, `prices[].item_id`, `active`/`completed` bools, `version`, `nextPage`, explicit segment metadata.

### Phase 10: Traderie pagination/window discovery
- Fetched 10 sequential pages for Jah pc_sc_nl (waiting 2s between).
- **Critical finding:** All 10 pages returned the same 50 listings. `nextPage` is boolean/repeating, not a real cursor.
- `completed=true` returns a rolling ~50-listing window. For high-volume items, this spans ~7 hours. For low-volume items, it spans weeks to months.
- Window behavior: `rolling_recent_trades_50_cap`.
- Implication: history can only be built by scheduled polling — no backfill via pagination.

### Phase 11: Snapshot/history infrastructure
- Created `scripts/lib/snapshot_io.py` with `write_raw_snapshot`, `write_normalized_snapshot`, `append_history`, `observation_key`, `content_hash`.
- ItemNow parser adopted as first user.
- Snapshot paths: `data/snapshots/raw/<source>/<ts>/`, `data/snapshots/normalized/<source>/<ts>.json`
- History paths: `data/history/<source>/<dataset>.jsonl`
- All snapshot/history paths gitignored.

### Phase 12: Traderie snapshot collector
- Created `scripts/snapshot_traderie.py` — iterates all 4 segments × all items, writes snapshots + history + legacy raw files.
- Created `scripts/run_traderie_snapshot_launchd.sh` — bash runner with `mkdir`-based atomic lock, per-segment error handling.

### Phase 13: Launchd setup and installation
- Namespace: `com.buddy.traderie.*` (confirmed free before install).
- Label: `com.buddy.traderie.snapshot-traderie`
- Schedule: 05:00 / 11:00 / 17:00 / 23:00 (avoids existing 03:00-03:30 buddy jobs).
- Plist validated: `plutil -lint OK`.
- Shell script validated: `bash -n OK`.
- Lock mechanism: `mkdir` atomic lock (flock not available on macOS).
- Installed, loaded, kickstarted. First run: pc_sc_nl ✅, pc_sc_l ✅, pc_hc_l ⚠️ (timeout on one item), pc_hc_nl ❌ (timeout on first fetch). Retry: ✅.
- No other launchd labels were touched.

### Phase 14: Static UI scaffold
- Created `web/` — Vite 8 + React 19 + TypeScript + react-router-dom.
- 4 pages: `/` (market overview), `/runes` (full dashboard), `/sources` (directory), `/about-methodology`.
- Data-driven: all JSON imports from `@data/` alias pointing to `../data/`.
- Segment selector via URL query param `?segment=pc_sc_nl`.
- Cash column visually separated from in-game column. Cash disclaimer on every page.
- Diablo2.io labeled research-only/thin signal.
- Build: ✅ 0 tsc errors, production build ~100KB gzip.

---

## C. Source Status Table

| Source | Status | Priority | Role | Use in Model |
|---|---|---|---|---|
| **Traderie** | integrated | tier_1 | Canonical completed-trade model (rolling 50-cap) | Primary |
| **IGGM** | parser_prototype_ready | tier_2 | Cash comparison (30 obs, high segment confidence) | false |
| **ItemNow** | parser_prototype_ready | tier_3 | Cash comparison (42 obs, WooCommerce API) | false |
| **D2Stock** | parser_prototype_ready | tier_3 | Cash comparison (199 obs, RSS/XML, 2 segments) | false |
| **Diablo2.io** | parser_prototype_ready | tier_1 | Research: 14 candidate rows, 12 clean, thin signal | false |
| **MuleFactory** | captured_static | tier_3 | Cash parser candidate (24 runes, static microdata) | false |
| **Eldorado** | captured_browser | tier_3 | Cash parser candidate (476 listings, rendered) | false |
| **MMOPixel** | captured_browser | tier_3 | Cash parser candidate (1,304 items, rendered) | false |
| **PlayerAuctions** | captured_browser | tier_3 | Cash active listings, deferred (needs browser) | false |
| **G2G** | captured_browser | tier_2 | Cash marketplace, taxonomy unresolved | false |
| **items7** | captured_static | tier_3 | 0 parseable rows, needs browser capture | false |
| **YesGamers** | deferred | tier_3 | Login wall | false |
| **d2jsp** | deferred | later | Fully gated (Cloudflare + login). FG economy separate | false |
| **RPGStash** | captured_static | later | Camoufox crashes, needs manual capture | false |
| **eBay** | discovered | later | Anti-bot blocks all automation | false |
| **Reddit** | deferred | tier_3 | Qualitative only | false |
| **Discord** | discovered | later | Gated/manual downstream research only | false |
| All other sources | discovered | later | Zero artifacts, caveated unproven | false |

---

## D. Product/Data Status

| Product | Observations | Segments | Source | Window Label |
|---|---|---|---|---|
| `in_game_rune_values.json` | 92 rune obs, 2,570 modeled trades | 4 (pc_sc_l, pc_sc_nl, pc_hc_l, pc_hc_nl) | Traderie | rolling_recent_trades_50_cap |
| `traderie_tools_prices.json` | 92 rune obs | 4 | Traderie | rolling_recent_trades_50_cap |
| `external_cash_prices.sample.json` | 271 obs | source-specific | IGGM (30) + ItemNow (42) + items7 (0) + D2Stock (199) | current_snapshot |
| `rune_registry.json` | 33 runes, id 1-33, 3 tiers | N/A | Canonical | N/A |

### Confidence counts (in-game)
- High: 12 (50+ trades)
- Medium: 7 (15-49 trades)
- Low: 30 (1-14 trades)
- Unavailable: 43 (0 trades)

### Snapshot/history (ignored, not committed)
- Traderie snapshots: 4 segments, ~1,600+ normalized observations appended
- ItemNow: 3 snapshot runs, 84 history entries
- Traderie launchd log: recorded

---

## E. Key Technical Findings

1. **Traderie `completed=true` is a rolling 50-cap window.** `nextPage` is boolean/repeating, not a real cursor. High-volume items cycle ~7h. Low-volume items retain listings for weeks to months. No pagination-based backfill possible.

2. **Diablo2.io sold-search volume is too low for modeling.** Jah (7 rows), Ber (2), Lo (3), Sur (2). Page 2 doesn't exist for any — all show "Page 1 of 1". The sold-search surface is a thin reference signal at best.

3. **ItemNow WooCommerce Store API is the cleanest public endpoint found.** No auth, no JS rendering, 42 products with prices and segment attributes. 9/10 parseability.

4. **D2Stock RSS feed is the largest cash source by volume.** 199 observations across 2 segments with segment-specific pricing. Google Shopping XML format.

5. **d2jsp is fully gated.** Cloudflare blocks curl. Camoufox confirms login wall with 0 visible topic titles. FG (Forum Gold) economy cannot be evaluated without login access.

6. **Cash sources are current-only.** None expose historical prices. Snapshotting is the only way to build cash price history.

7. **macOS `flock` is not available.** Replaced with `mkdir`-based atomic locking in the launchd runner.

---

## F. Launchd Operational State

| Property | Value |
|---|---|
| Namespace | `com.buddy.traderie.*` |
| Label | `com.buddy.traderie.snapshot-traderie` |
| Schedule | 05:00 / 11:00 / 17:00 / 23:00 |
| Plist location | `launchd/com.buddy.traderie.snapshot-traderie.plist` |
| Installed at | `~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist` |
| State | Loaded, idle (waiting for next schedule) |
| Last run exit code | 1 (one segment had transient timeout; retry succeeded) |
| Lock mechanism | `mkdir` atomic lock (not flock) |
| Shell script | `scripts/run_traderie_snapshot_launchd.sh` |
| Stdout log | `logs/launchd/snapshot-traderie.out.log` |
| Stderr log | `logs/launchd/snapshot-traderie.err.log` |
| Lock path | `.run/locks/snapshot-traderie.lock` |
| Install command | `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist` |
| Safety | No other launchd labels touched. Namespace isolated. |

### ⚠️ Operational Caveat

The launchd job `com.buddy.traderie.snapshot-traderie` is **installed and active on this machine** (`~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist`). The committed plist at `launchd/com.buddy.traderie.snapshot-traderie.plist` is the source template. The runtime installation in `~/Library/LaunchAgents/` is the operational copy.

**Future agents must not:**
- Run `launchctl bootstrap`, `bootout`, `kickstart`, `unload`, `remove`, or `restart` on any label unless explicitly asked by the user.
- Modify, delete, or replace any plist in `~/Library/LaunchAgents/` outside the `com.buddy.traderie.*` namespace.
- Touch any existing launchd label outside `com.buddy.traderie.*`.
- Run broad launchctl commands (e.g., `launchctl unload` without a specific label).

**Safe inspection commands:**
- `launchctl print gui/$(id -u)/com.buddy.traderie.snapshot-traderie` — check state
- `launchctl list | grep com.buddy.traderie` — check label exists
- `ls ~/Library/LaunchAgents/com.buddy.traderie*` — check plist installed

**Do not modify scheduler state** unless the user explicitly asks to install, uninstall, or modify the schedule.

---

## G. Commit Log (newest first)

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
The 7 milestone commits are 6579232 through cdd55f9. The 2 earlier commits (013c994, ce2eba0) were from the initial repo setup before this session.

---

## H. Validation Status

- **Last full green smoke test:** `research/memos/2026-06-20-integration-smoke-test.md`
  - validate_source_manifest.py: ✅ 20 sources valid
  - validate_external_cash_prices.py: ✅ 271 obs, 4 sources, schema v0.2
  - validate_in_game_rune_values.py: ✅ both products
  - parse_itemnow_api.py: ✅ 42 products
  - parse_d2stock_rss.py: ✅ 199 obs
  - generate_external_cash_prices.py: ✅ 271 merged
  - generate_prices_json.py: ✅ 4 segments, 92 obs, 2,570 trades
  - snapshot_traderie.py --segment pc_sc_nl --item "Jah Rune": ✅ 50 listings, 50 unique IDs
  - web build: ✅ 0 tsc errors, ~100KB gzip
- **Git Steward validations blocked** by permission model (only git commands allowed).
- **Launchd shell script:** `bash -n` OK.
- **Plist:** `plutil -lint` OK.

### 💡 Validation Artifact Note

The smoke test memo `research/memos/2026-06-20-integration-smoke-test.md` is **not currently committed** (it was created during the session and remains untracked). To make this session log's validation claims verifiable by a future agent:
- Option A: Commit the smoke test memo alongside this log.
- Option B: Remove the per-check breakdown and note "validation known passing at session close, see session log."

**Recommendation: Commit the smoke test memo with this log.** The smoke test is the single best evidence that the full pipeline was passing at milestone end. Without it, readers of this log must trust the claims without reproducible proof.

---

## I. What Remains Untracked / Scratch

| Pattern | Files | Status | Recommendation |
|---|---|---|---|
| `docs/PROJECT_MEMORY.md` | 1 modified | Scratch | Leave untracked — session scratch. Will diverge from commit log. |
| `docs/TRADERIE_*.md` | 3 untracked | Scratch | Traderie integration session docs. Commit if promoted to permanent docs; otherwise clean up. |
| `data/research/*.sample.json` | 7 untracked | Scratch | Per-rune probe outputs, API probe samples. Not linked by any committed doc. May be cleaned. |
| `research/memos/*probe*.md` | 3 untracked | **Should commit** | PlayerAuctions, player-community, zero-artifact probe memos. These are durable research findings, not scratch. |
| `research/memos/2026-06-20-integration-smoke-test.md` | 1 untracked | **Should commit** | Smoke test evidence. The session log relies on this for validation claims. |
| `research/sources/captures/` (non-D2io) | ~10 dirs | Scratch | Probe screenshots, metadata, browser captures. Large/binary. Clean up eventually. |
| `research/sources/captures/diablo2io/*/screenshot.png` | 4 screenshots | Scratch | Browser captures. Not needed for reproducibility. |
| `research/sources/captures/diablo2io/*/metadata.json` | 4 metadata files | Scratch | Capture timestamps. Low value. |
| `scripts/capture_with_camoufox.py` | 1 untracked | Scratch | Experimental Camoufox wrapper. Not documented or maintained. |
| `web/src/assets/` | 2 files | Scratch | Vite template boilerplate (hero.png, vite.svg) — not referenced by UI. |

**Total remaining untracked:** ~35 files / directories. All are probe artifacts, screenshots, session scratch, or experimental utilities. None are blocking reproducibility.

---

## J. Next Recommended Actions

Prioritized:

1. **Let launchd run for 24h.** Check history growth across all 4 segments. Verify no lock contention. Adjust cadence if needed.

2. **Add collection status script/page.** Quick `scripts/collection_status.py` that reads snapshot/history dirs and prints last-run times, observation counts per segment, total history size. Optional: add a simple `/status` route to the web UI.

3. **Regenerate products from retained history.** After sufficient snapshots accumulate, test whether the existing `extract → model → generate` pipeline produces stable or improved prices from larger N.

4. **Polish UI.** The static scaffold is functional but minimal. Priority: source freshness/window caveats visible, confidence tooltips, responsive layout improvements.

5. **Add cash parsers for MuleFactory/Eldorado later.** Cash coverage is already strong (271 obs). Additional sources add breadth but not core value. Only do if specific gaps emerge (e.g., Ladder/Hardcore segment prices not covered by current sources).

6. **Do not prioritize Diablo2.io sold-search further.** The volume ceiling is structural, not fixable. One exception: probing the item price history page (`misc/jah-t43.html` with "Total results: 2812") may yield more data, but with less context per row. Low priority.

7. **Commit session log companion files.** The session log's validation and research claims rely on:
   - `research/memos/2026-06-20-integration-smoke-test.md` — validation evidence
   - `research/memos/2026-06-20-playerauctions-rune-specific-probe.md` — probe finding
   - `research/memos/2026-06-20-player-community-source-probes.md` — probe finding
   - `research/memos/2026-06-20-zero-artifact-cash-source-probes.md` — probe finding
   These should be committed alongside this log for reproducibility. The session log itself (`research/memos/2026-06-20-session-log-market-pipeline-milestone.md`) should also be committed.

8. **Clean up probe artifacts.** The 30+ remaining untracked items (screenshots, probe sample JSONs, non-D2.io capture artifacts, experimental scripts, Vite template assets) should be cleaned or left untracked. None are critical for reproducibility.
