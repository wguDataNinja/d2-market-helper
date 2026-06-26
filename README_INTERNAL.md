# README_INTERNAL — D2R Market Helper (Traderie)

> Last updated: 2026-06-26 (comprehensive post-audit update)
> Status: active — pipeline running, softcore stable, hardcore fragile, regen automated, web deploy ready
> Owner: Buddy

---

## Repo Identity

**Name:** traderie
**Product:** D2R Market Helper
**Purpose:** Multi-source market intelligence hub for Diablo II: Resurrected traders. Collects completed trades from Traderie.com, calculates Ist-normalized rune prices per economy segment, and publishes to a web dashboard + companion Tampermonkey userscript.
**Canonical plan:** `ROADWAY.md` (completed — all sessions done)
**Auth docs:** `AGENTS.md`, `SESSION.md`, `LOG.md`

---

## Quick Status

| Component | Status |
|-----------|--------|
| Snapshot pipeline | Running 4x daily via launchd |
| Softcore segments (pc_sc_l, pc_sc_nl) | ✅ Green — exit 0 every run |
| Hardcore segments (pc_hc_l, pc_hc_nl) | ⚠️ WARNING — ReadTimeout expected, exit 0 (softcore-critical exit code) |
| Product regeneration | ✅ Automated — launchd plist loaded, daily 06:00 |
| Products freshness | Fresh — generated 2026-06-26T07:38:40Z |
| Web dashboard | Built, SPA routing fixed, deploy workflow ready |
| AND trade modeling | Done (proportional decomposition, capped at 2-item) |
| Game version / Ruleset | ✅ Pipeline captures game_version + ruleset, API filtering via `--ruleset`, metadata in products |
| Ruleset-split pricing | ❌ Not started — ROTW dominates (>95%), LoD/classic too thin |
| Non-Ist rune pair audit | Done — 4,995 non-Ist trades analyzed, Jah↔Ber 1:1 confirmed, 33% divergence vs Ist-only model |
| Graph pricing prototype | Research-only — scipy_nnls solver, confirms Jah/Ber parity signal but unstable from outliers |
| External userscript | Patched — feed cache, segment safety, complexity labels, confidence surfacing |
| Cash price data | 295 obs across 5 sources, comparison-only |
| GitHub Pages deploy | Prepared — 404.html SPA fallback, GH Actions workflow, data files in public/ |

---

## Pipeline Architecture

```
Traderie API (4 segments, 4x daily via launchd)
  └─ snapshot_traderie.py (fetch raw listings)
       ├─ supports --ruleset rotw|lod|classic for API-level Game version filtering
       ├─ extracts game_version + ruleset from listing.properties[]
       ├─ exit semantics: softcore failures → exit 1 (critical), hardcore → exit 0 (warning)
       ├─ data/snapshots/raw/traderie/{seg}/{ts}/response.json
       ├─ data/snapshots/normalized/traderie/{seg}/{ts}.json
       └─ data/history/traderie/{seg}/completed_trades_{seg}.jsonl
              │
              ▼ (daily 06:00 via launchd: com.buddy.traderie.regenerate-products)
       ├─ build_traderie_dataset_from_history.py
       │    └─ data/research/extracted_trades_{seg}.csv (includes game_version, ruleset)
       ├─ calculate_rune_prices.py
       │    └─ data/prices/rune_prices_{seg}.csv
       ├─ generate_prices_json.py
       │    ├─ data/products/in_game_rune_values.json (includes ruleset_breakdown per segment)
       │    └─ data/products/traderie_tools_prices.json
       ├─ generate_external_cash_prices.py
       │    └─ data/products/external_cash_prices.sample.json
       └─ validation (runs during regeneration):
            ├─ validate_in_game_rune_values.py
            ├─ validate_external_cash_prices.py
            ├─ validate_source_manifest.py
            └─ collection_status.py
```

---

## Economy Segments

Four segments, strictly separated — never merged:

| Segment | Platform | Mode | Hardcore | Ladder | Trades | Runes Priced |
|---------|----------|------|----------|--------|--------|-------------|
| pc_sc_l | PC | Softcore | No | Yes | 2,342 | 23 |
| pc_sc_nl | PC | Softcore | No | No | 804 | 23 |
| pc_hc_l | PC | Softcore | Yes | Yes | 79 | 23 |
| pc_hc_nl | PC | Softcore | Yes | No | 38 | 23 |

All PC only. Console segments exist in `source_manifest.json` but are not price-tracked.

---

## Ruleset / Game Version Breakdown

Per the 2026-06-26 raw-snapshot audit (108,660 listings across 4 segments):

| Segment | Classic | LoD | ROTW | Mixed | Unknown | Dominant |
|---------|---------|-----|------|-------|---------|----------|
| pc_sc_l | 26 | 148 | 26,120 | 0 | 6 | ROTW (99.5%) |
| pc_sc_nl | 13 | 1,090 | 30,791 | 26 | 80 | ROTW (96.2%) |
| pc_hc_l | 149 | 100 | 25,847 | 101 | 9,711 | ROTW (72.1%) |
| pc_hc_nl | 0 | 358 | 5,478 | 0 | 8,616 | Unk (59.6%) — hardcore failures |

Game version is filterable via the completed-trades API: `prop_Game%20version=lord+of+destruction` etc. The `--ruleset` flag on `snapshot_traderie.py` uses this.
Region (Americas/Europe/Asia) is **not available** in completed-trades API data — visible only in the web UI.

---

## Non-Ist Rune Pair Audit

A May 2026 audit (`scripts/audit_rune_pairs.py`) found:

- **4,995 non-Ist rune trades** (40-70% of extracted rows) are completely ignored by the Ist-only pricing model
- **Jah↔Ber 1:1 is the single most common high-rune trade pattern**:
  - pc_sc_l: 427 Jah↔Ber 1:1 trades
  - pc_sc_nl: 64
  - pc_hc_l: 25
  - pc_hc_nl: 9
- **Current Ist-only model reports Ber ≈ 1.49× Jah** in softcore, while players trade them 1:1
- **33% divergence** between Ist-anchored prices and direct trade observations

### Graph Pricing Prototype

A research-only prototype (`scripts/prototype_graph_rune_prices.py`) solves a graph of all rune trades using `scipy.optimize.nnls`:

| Segment | Production Ber/Jah | Graph Ber/Jah | Direct trade evidence |
|---------|:---:|:---:|:---:|
| pc_sc_l | 1.49 | 0.86 | 401 Ber→Jah 1:1 trades |
| pc_sc_nl | 1.49 | 0.50 | 64 Jah↔Ber 1:1 trades |
| pc_hc_nl | 0.21 | 0.66 | 9 Jah↔Ber 1:1 trades |

**Verdict: Research-only.** Directionally useful for pc_sc_l (moves toward parity), but unstable due to extreme outlier equations (e.g., `Ist:99 -> Jah:9`). Needs robust loss, outlier filtering, and sane bounds before any production consideration.

---

## What Data Exists

### Product files

| File | Size | Contents |
|------|------|----------|
| `data/products/in_game_rune_values.json` | ~38 KB | Per-segment rune prices + ruleset_breakdown metadata |
| `data/products/traderie_tools_prices.json` | ~19 KB | Userscript format (ist_value, bid, ask, total_trades, confidence) |
| `data/products/external_cash_prices.sample.json` | ~403 KB | 295 cash observations across 5 sources, use_in_model=false |
| `data/products/rune_prices_legacy.json` | ~17 KB | Legacy flat format for old userscript versions |

### Per-rune price fields

```json
{
  "rune": "Ohm",
  "value_ist": 3.446,
  "bid_price": 3.0647,
  "ask_price": 3.8273,
  "bid_count": 314,
  "ask_count": 265,
  "total_trades": 579,
  "confidence": "high",
  "confidence_reason": "Based on 579 trades"
}
```

### Ruleset metadata in product

Each segment now has a `ruleset_breakdown` block:

```json
"ruleset_breakdown": {
  "counts": { "classic": 26, "lod": 148, "rotw": 26120, "unknown": 6 },
  "total_observed_raw_listings": 26300,
  "dominant_ruleset": "rotw",
  "dominant_ruleset_share": 0.993
}
```

### History accumulation

| Segment | Raw lines | Unique IDs | Approx runs |
|---------|-----------|-------------|-------------|
| pc_sc_l | 38,500 | 12,699 | ~12-14 |
| pc_sc_nl | 38,650 | 6,076 | ~12-14 |
| pc_hc_l | 38,158 | 2,235 | ~12-14 |
| pc_hc_nl | 15,044 | 1,104 | ~6-8 |

300 game-version-labeled rows appended via controlled ruleset collection (rotw + lod across softcore, rotw on hc_l).

---

## Launchd Jobs

| Label | Loaded? | Schedule | Last run | Status |
|-------|---------|----------|----------|--------|
| `com.buddy.traderie.snapshot-traderie` | ✅ Loaded | 05:00, 11:00, 17:00, 23:00 | Recent — exit code 1 (hardcore failures, softcore succeed) | ⚠️ Hardcore warning (exit 0 since patch) |
| `com.buddy.traderie.regenerate-products` | ✅ Loaded | 06:00 daily | Never run yet (installed 2026-06-26) | ✅ Loaded, scheduled |

Both plists pass `plutil -lint`. The regen plist was bootstrapped into the user GUI namespace via `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.buddy.traderie.regenerate-products.plist`.

---

## Web Dashboard

**Stack:** React 19 + Vite 8 + TypeScript + React Router 7. Data loaded as static JSON imports at build time (also copied to `web/public/data/` for runtime userscript fetch).

**Routes:** `/` (Market Overview), `/runes` (Rune Dashboard), `/sources` (Source Directory), `/about-methodology` (Methodology)

**GitHub Pages deployment prepared:**
- `scripts/deploy_web.sh` — copies product JSONs to `public/data/`, runs `npm build`
- `.github/workflows/deploy.yml` — GH Actions workflow: checkout → npm ci → copy data → build → upload → deploy Pages
- `web/public/404.html` — SPA redirect fallback for client-side routing
- `web/src/main.tsx` — sessionStorage redirect handler for GitHub Pages 404 recovery
- Methodological caveats added: Game version/ruleset limitations, region unavailability

**Blocked on:** No GitHub remote configured. Once remote is set and Pages enabled (Source: GitHub Actions), push to `master` triggers deploy.

---

## External Userscript

**Repo:** `github.com/wguDataNinja/TraderieTools` (cloned at `/Users/buddy/projects/TraderieTools`)

Patched 2026-06-26:
- **@version** bumped to `2026-06-26`
- **Feed cache**: localStorage cache (`D2RMH_PRICE_CACHE_V1`) with 1h TTL, stale fallback on errors
- **Segment safety**: `resolveServerSegment()` returns explicit/absent/unsupported; no silent pc_sc_nl default
- **Rune parser**: handles bare `"Ber Rune"` (qty 1) plus `"1x Ber Rune"` and NBSP variants
- **Complexity handling**: AND/bundle trades show "Complex trade — review manually" (not scored)
- **State labels**: Good for you / Fair range / Likely overpay / Unavailable / Low confidence
- **SPA hooks**: popstate + pushState/replaceState interception with 200ms debounce
- **CSS**: namespaced `.d2rmh-badge-*` classes, no interference with existing adblock/bookmark CSS

**Feed shape support:** Legacy `{slug: {name: {ist_value}}}`, structured `{segments: {slug: {runes: ...}}}`, and future wrapped segment shapes all handled.

---

## Known Issues

### Critical

1. **Hardcore segment ReadTimeout** — pc_hc_nl fails every item fetch, pc_hc_l fails ~50% of items. `HARDCORE_REQUEST_TIMEOUT_SECONDS=20` (not 30 as README says). Pipeline exits 0 for hardcore-only failures (post-patch).

2. **No alerting on failures** — errors silently logged to err.log only. No email/push/GH notification.

### Moderate

3. **AND trade modeling done but methodology docs say otherwise** — Methodology page and some docs still reference "AND trades excluded" wording. Products include proportional decomposition.

4. **Graph pricing prototype unstable** — OLS over raw equations produces near-zero values in pc_sc_nl and clips Mal to 0.0 in pc_hc_l. Needs outlier filters and robust loss before any production consideration.

5. **Region data unavailable** — Completed-trades API has no region dimension (Americas/Europe/Asia). Visible in Traderie web UI but cannot be extracted for pricing.

6. **Historical rows pre-2026-06-26 have ruleset=unknown** — Rows before the game_version patch show unknown. Recoverable from raw snapshot response.json files.

7. **No GitHub remote configured** — Cannot push or deploy the web dashboard.

8. **Diablo2.io not integrated** — 14 candidate rows, parser exists but not validated.

9. **items7 blocked** — requires browser capture, not automated.

10. **Sur and Vex absent from rune catalog** — Not in `data/item_ids.json`, no trades in extracted CSVs.

---

## Roadmap Progress

| Session | Topic | Status | Notes |
|---------|-------|--------|-------|
| 1-6 | Original roadmap sessions | ✅ All done | Doc refresh, AND trades, MuleFactory, operational hardening, hardcore probe, validation |
| 7 | Game version / ruleset | ✅ Done | Pipeline capture, API-level filtering, product metadata |
| 8 | Exit code hardening | ✅ Done | Softcore critical (exit 1), hardcore warning (exit 0) |
| 9 | Regen launchd plist | ✅ Done | Bootstrapped and loaded, daily 06:00 |
| 10 | GH Pages deploy | ✅ Done | Workflow, 404.html, deploy script, methodology — blocked on remote |
| 11 | Non-Ist pair audit | ✅ Done | 4,995 trades analyzed, Jah↔Ber divergence confirmed |
| 12 | Graph pricing prototype | ⚠️ Research | scipy_nnls solver, Jah/Ber signal confirmed, unstable from outliers |
| 13 | Userscript patch | ✅ Done | Cache, segment safety, complexity labels, state labels, SPA hooks |
| 14 | Ruleset-split pricing | ❌ Not started | ROTW dominates; low non-ROTW volume |

---

## Open Decisions for Buddy

- [ ] Create GitHub repo and add remote → deploy web dashboard
- [ ] Hardcore gap root cause (timeout vs zero-listings distinction)
- [ ] Graph pricing v2 with outlier filters and robust loss
- [ ] Alerting mechanism (macOS notification? GH Actions?)
- [ ] D2Stock/IGGM snapshot integration
- [ ] Diablo2.io validation
- [ ] Non-rune item expansion priority

---

## Key Paths

| What | Path |
|------|------|
| Launchd installed snapshot plist | `~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist` |
| Launchd installed regen plist | `~/Library/LaunchAgents/com.buddy.traderie.regenerate-products.plist` |
| Plist templates | `launchd/*.plist` |
| Snapshot runner | `scripts/run_traderie_snapshot_launchd.sh` |
| Collect trades | `scripts/snapshot_traderie.py` (supports `--ruleset`, `--dry-run`) |
| Regen script | `scripts/regenerate_products.sh` (scheduled by launchd) |
| Deploy script | `scripts/deploy_web.sh` |
| History builder | `scripts/build_traderie_dataset_from_history.py` |
| Price calculator | `scripts/calculate_rune_prices.py` |
| Product generator | `scripts/generate_prices_json.py` |
| Cash generator | `scripts/generate_external_cash_prices.py` |
| Non-Ist pair audit | `scripts/audit_rune_pairs.py` |
| Graph prototype | `scripts/prototype_graph_rune_prices.py` |
| Web app | `web/` (src at `web/src/`) |
| GH Actions workflow | `.github/workflows/deploy.yml` |
| Game version audit | `scripts/audit_traderie_game_version.py` |
| Extern userscript | `/Users/buddy/projects/TraderieTools/traderie-tools.user.js` |
| stdout log | `logs/launchd/snapshot-traderie.out.log` |
| stderr log | `logs/launchd/snapshot-traderie.err.log` |

---

## Commands

```bash
# Snapshot (data collection):
python3 scripts/snapshot_traderie.py --segment pc_sc_l
python3 scripts/snapshot_traderie.py --segment pc_sc_nl --ruleset lod
python3 scripts/snapshot_traderie.py --segment pc_sc_l --ruleset rotw --dry-run

# Product regeneration (manual or daily 06:00 via launchd):
bash scripts/regenerate_products.sh

# Validation:
python3 scripts/validate_source_manifest.py
python3 scripts/validate_in_game_rune_values.py
python3 scripts/validate_external_cash_prices.py
python3 scripts/collection_status.py

# Web app:
npm --prefix web run dev
npm --prefix web run build
bash scripts/deploy_web.sh

# Audits/research:
python3 scripts/audit_traderie_game_version.py
python3 scripts/audit_rune_pairs.py
python3 scripts/prototype_graph_rune_prices.py

# Launchd (do NOT run without approval):
launchctl list | grep traderie
```

---

## Watchouts

- Never blend cash-market prices into in-game rune values. Cash is always `use_in_model=false`.
- Never merge economy segments (PC SC L ≠ PC SC NL ≠ PC HC L ≠ PC HC NL).
- Do not run `launchctl bootstrap` or `launchctl bootout` without explicit Buddy approval.
- Do not touch the external TraderieTools userscript repo unless explicitly asked.
- `data/history/` is large and gitignored — do not git add.
- `data/snapshots/` is large and gitignored — do not git add.
- `web/public/data/` is gitignored (regenerated by deploy script).
- `data/research/` is gitignored (regenerated by history builder and research scripts).
- Graph pricing prototype is research-only — do not use for production pricing.
- Hardcore segment failures are expected (thin economy) — collection_status.py surfaces warnings.
- No GitHub remote configured yet — web dashboard cannot be deployed.
