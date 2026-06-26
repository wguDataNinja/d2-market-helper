# Traderie Ship Plan

Goal: get traderie to a fully automated daily pipeline with a published price site and downloadable Traderie companion userscript/feed, without weakening the core invariants:

- Never blend cash-market prices into in-game rune values.
- Never merge economy segments: `pc_sc_l`, `pc_sc_nl`, `pc_hc_l`, `pc_hc_nl`.
- Keep raw/history data private; publish only schema-versioned products and static site assets.

## 1. Current State Assessment

### What works

- **Snapshot fetching exists and is scheduled.** `launchd/com.buddy.traderie.snapshot-traderie.plist` runs `scripts/run_traderie_snapshot_launchd.sh` at 05:00, 11:00, 17:00, and 23:00. The runner uses a macOS-safe `mkdir` lock and calls `scripts/snapshot_traderie.py` once per segment.
- **Snapshot retention is integrated.** `scripts/snapshot_traderie.py` writes raw snapshots, normalized snapshots, history JSONL, and backward-compatible raw files. It captures seller metadata, listing IDs, `completed`, segment metadata, `prices[].item_id`, AND-price flags, and group counts.
- **History-to-products path exists.** `scripts/regenerate_products.sh` runs:
  - `scripts/build_traderie_dataset_from_history.py --write-research`
  - `scripts/calculate_rune_prices.py --input-dir data/research`
  - `scripts/generate_prices_json.py`
  - `scripts/generate_external_cash_prices.py`
  - validators and `scripts/collection_status.py`
- **Extraction and calculation are implemented.** The history builder dedupes by listing ID, extracts valid rune-for-rune rows, preserves `price_groups_json`, and writes per-segment research CSVs. The calculator already decomposes two-item AND requests and excludes larger multi-item requests.
- **Public products exist.** Current products were generated at `2026-06-23T04:25:27Z`:
  - `data/products/in_game_rune_values.json`: 4 segments, 92 rune observations, 1,991 total modeled trades.
  - `data/products/traderie_tools_prices.json`: 4 segments, userscript-compatible schema v0.2.
  - `data/products/external_cash_prices.sample.json`: 295 cash observations across IGGM, ItemNow, D2Stock, MuleFactory, and items7.
- **Validation scripts exist.** There are validators for in-game products, external cash products, and source manifest integrity.
- **Web dashboard exists.** `web/` is a Vite/React app with pages for market overview, rune dashboard, source directory, and methodology. It imports data from `data/products/*.json`, `data/source_manifest.json`, and `data/rune_registry.json`.
- **Userscript feed docs exist.** `docs/USERSCRIPT.md` documents `traderie_tools_prices.json` and `rune_prices_legacy.json`, segment detection, safety rules, and feed deployment.

### What's broken

- **Hardcore snapshot reliability is still not acceptable.**
  - `collection_status.py --json` reports `pc_hc_nl` as stale even though a normalized snapshot file exists from `2026-06-25T03:12:51Z`; its latest observed trade timestamp is `2026-06-24T06:36:07.270Z`.
  - Recent launchd output shows repeated `ReadTimeout` failures in hardcore segments. `pc_hc_l` often fails on `Amn Rune`; `pc_hc_nl` repeatedly fails on items such as `Ohm Rune`, `Ral Rune`, `Perfect Ruby`, `Perfect Amethyst`, and `Token of Absolution`.
  - `scripts/snapshot_traderie.py` exits 1 if any item fails. That is good for visibility but means partial hardcore failures make the full launchd run fail.
- **Regeneration automation is present but not operationally loaded.**
  - `launchd/com.buddy.traderie.regenerate-products.plist` exists and points to `scripts/regenerate_products.sh` at 06:00.
  - The prompt states the plist is not loaded. No launchctl mutation should be run unless Buddy explicitly asks.
- **Products are stale relative to current snapshots.**
  - Products are from `2026-06-23T04:25:27Z`; collection status was inspected on `2026-06-25T08:12:17Z`.
  - Snapshot history has grown since product generation, but the public JSON has not been rebuilt automatically.
- **Docs/UI drift exists.**
  - `generate_prices_json.py` caveats mention approved AND handling, but `docs/USERSCRIPT.md` and `web/src/pages/Methodology.tsx` still say AND trades are excluded.
  - This does not block the pipeline, but it will confuse public users if the site is published as-is.

### What's missing

- **No failure alerting.** `collection_status.py` can detect stale segments and log timeouts, but nothing notifies Buddy when snapshot or regeneration fails.
- **No published site.** `web/dist/` exists, but there is no deployed static host or documented publish workflow.
- **No public userscript download/update URL.** The external TraderieTools repo is documented, but the project does not yet publish an installable `.user.js` or stable update/feed URL from the price site.
- **No end-to-end ship check.** There is no single daily proof that snapshot, regeneration, validation, web build, and publish all completed.

### Risk assessment of running with current errors

| Risk | Impact | Severity |
|---|---:|---:|
| Hardcore item failures keep launchd exit code at 1 | Daily automation appears failed even when softcore data is fresh | High |
| Product regeneration is not loaded | Public JSON and userscript feed go stale silently | High |
| No alerting | Buddy learns about failures only by manual inspection | High |
| Publishing current products | Site would show stale data from `2026-06-23` and thin/stale hardcore coverage | Medium |
| Docs/UI drift around AND handling | Users may misunderstand what the model includes | Medium |
| Publishing raw/history artifacts by accident | Could expose private operational data | High, but avoidable with static publish allowlist |

## 2. Fix Pipeline First

Do this before site/userscript publication. The project should not publish a daily price site until snapshot runs and regeneration have deterministic behavior.

### Objective

Get the scheduled snapshot job to finish with a clear, expected exit status and enough data freshness to support daily product regeneration.

### Work items

| Item | Action | Validation | Estimate | Risk |
|---|---|---|---:|---|
| Confirm installed runner is current | Inspect only: confirm launchd label points at `/Users/buddy/projects/traderie/scripts/run_traderie_snapshot_launchd.sh`, and that the installed job is not using an old `flock` runner. Do not mutate launchctl unless asked. | `launchctl print gui/$(id -u)/com.buddy.traderie.snapshot-traderie` shows current path; logs no longer show new `flock: command not found` lines. | 0.25 day | Low |
| Classify hardcore failures | Run targeted probes for recent failing hardcore items: `Amn Rune` on `pc_hc_l`; `Ohm Rune`, `Ral Rune`, `Perfect Ruby`, `Perfect Amethyst`, `Token of Absolution`, and any current skipped `pc_hc_nl` items. | Per-item logs show whether each failure is persistent timeout, intermittent timeout, zero-listing success, or non-timeout API error. | 0.5 day | Medium |
| Decide skip/quarantine policy | For items that fail persistently, either skip them per segment or quarantine them into a failed-item report while allowing segment completion. Do not hide the exclusion; surface it in status output. | Full `scripts/snapshot_traderie.py --segment <seg>` returns 0 for all four segments or returns a documented nonzero only for true infrastructure failure. | 0.5-1 day | Medium |
| Separate item failure from job failure | Make the runner distinguish "partial item misses recorded" from "segment unusable." A segment should fail the full job only when too many items fail or no useful snapshot is written. | Launchd run exits 0 when failures are known/skipped/quarantined and freshness thresholds pass; exits 1 on Cloudflare/API/system failure. | 0.5 day | Medium |
| Refresh products after fixed snapshot | Run regeneration after the first clean snapshot cycle. | `validate_in_game_rune_values.py`, `validate_external_cash_prices.py`, and `collection_status.py --json` all pass; products have current `generated_at`. | 0.25 day | Low |

### Recommended success criteria

- `pc_sc_l`, `pc_sc_nl`, `pc_hc_l`, and `pc_hc_nl` each have a latest normalized snapshot from the current scheduled cycle.
- Snapshot job exits 0 for two consecutive scheduled cycles.
- Any skipped/quarantined item is explicitly listed by segment in `collection_status.py`.
- `pc_hc_nl` is allowed to remain thin, but it should not be silently stale.

## 3. Automate Regeneration

### Current state

- `scripts/regenerate_products.sh` exists and uses the repo virtualenv Python.
- `launchd/com.buddy.traderie.regenerate-products.plist` exists with label `com.buddy.traderie.regenerate-products`, working directory `/Users/buddy/projects/traderie`, stdout/stderr logs under `logs/launchd/`, and a 06:00 schedule.
- The prompt says the plist is not loaded. Treat loading as a Buddy-approved operational action, not a planning/editing action.

### Verification before loading

| Check | Command | Expected |
|---|---|---|
| Shell syntax | `bash -n scripts/regenerate_products.sh` | Exit 0 |
| Plist syntax | `plutil -lint launchd/com.buddy.traderie.regenerate-products.plist` | `OK` |
| Manual dry run | `scripts/regenerate_products.sh` | Products regenerated, validators pass |
| Product freshness | `python3 scripts/collection_status.py --json` | Product timestamps match run time |
| LaunchAgents target absent/present | `launchctl print gui/$(id -u)/com.buddy.traderie.regenerate-products` | Fails if not loaded, prints state if loaded |

### Load procedure after Buddy approval

1. Copy the plist to LaunchAgents:
   - `cp launchd/com.buddy.traderie.regenerate-products.plist ~/Library/LaunchAgents/`
2. Load it:
   - `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.buddy.traderie.regenerate-products.plist`
3. Optionally kickstart once:
   - `launchctl kickstart -k gui/$(id -u)/com.buddy.traderie.regenerate-products`
4. Inspect logs:
   - `tail -n 80 logs/launchd/regenerate-products.out.log`
   - `tail -n 80 logs/launchd/regenerate-products.err.log`

### Failure handling

- Keep `set -euo pipefail` so a failed build or validator fails the job.
- Write failures to `logs/launchd/regenerate-products.err.log`.
- Add alerting in Phase 4 that watches regeneration exit status, stale product timestamps, and validator failures.
- Do not publish new site assets if regeneration fails; keep the last valid site/feed online.

## 4. Publish Price Website

### Existing web dashboard

`web/` contains:

- Vite/React app with `npm --prefix web run build`.
- Source pages:
  - `web/src/pages/Home.tsx`
  - `web/src/pages/Runes.tsx`
  - `web/src/pages/Sources.tsx`
  - `web/src/pages/Methodology.tsx`
- Data loader:
  - `web/src/data/loader.ts` imports product JSON through `@data`.
- Build output:
  - `web/dist/index.html`
  - `web/dist/assets/*`

### Required before go-live

| Item | Action | Estimate |
|---|---|---:|
| Build verification | Run `npm --prefix web run build` after fresh products. | 0.25 day |
| Static routing | If using GitHub Pages, configure Vite `base` and routing so direct page loads do not 404. Easiest option: keep one-page hash routing or publish with SPA fallback. | 0.25-0.5 day |
| Data freshness display | Confirm the site visibly shows `product_generated_at`, `source_window_label`, segment, confidence, volume, and caveats. | 0.25 day |
| Correct methodology drift | Update public methodology/userscript wording to match current AND handling before launch. | 0.25 day |
| Publish allowlist | Publish only `web/dist/` plus intended JSON/userscript assets. Do not publish `data/history`, `data/snapshots`, raw logs, or `.env`. | 0.25 day |

### Hosting option

Use **GitHub Pages** first. It matches the static Vite app, avoids a server, and can publish generated `web/dist/` plus stable downloadable assets.

Recommended shape:

- Site root: static app from `web/dist/`.
- Data URLs:
  - `/data/in_game_rune_values.json`
  - `/data/traderie_tools_prices.json`
  - `/data/rune_prices_legacy.json`
  - Optional `/data/external_cash_prices.sample.json` if Buddy approves showing cash comparisons publicly.
- Userscript URLs:
  - `/userscript/traderie-tools.user.js`
  - `/userscript/traderie-tools.meta.js` if using Tampermonkey update metadata.

### Data to show

- Segment selector for all four PC segments.
- Search/filter by rune name.
- Per-rune fields:
  - Ist value
  - bid price
  - ask price
  - spread or bid/ask delta
  - modeled trade count
  - confidence badge
  - product freshness
- Segment-level summary:
  - total modeled trades
  - runes priced
  - unavailable runes
  - latest product generation time
- Cash comparison only if clearly labeled and separated from in-game values.

### Design simplicity

Keep launch scope to one static app with:

- Market Overview
- Rune Dashboard
- Sources
- Methodology
- Download Userscript link

Do not add accounts, server-side rendering, raw history browsing, or automated source discovery before launch.

## 5. Publish Companion Userscript

### Current state

- `docs/USERSCRIPT.md` says the userscript lives externally at `github.com/wguDataNinja/TraderieTools`.
- The repo generates:
  - `data/products/traderie_tools_prices.json`: structured v0.2 feed.
  - `data/products/rune_prices_legacy.json`: legacy flat feed.
- The external userscript repo should not be touched unless Buddy explicitly asks.

### Link vs embed

Recommended approach: **publish a downloadable copy on the same price site, with source-of-truth remaining in the external TraderieTools repo.**

Why:

- Users get one public install page.
- The userscript can use stable `@downloadURL` and `@updateURL`.
- The price data and userscript feed live under the same public origin.
- The external repo can remain the development source without exposing this repo's private runtime data.

### Versioning and update mechanism

Use Tampermonkey metadata:

```javascript
// @version      0.2.0
// @downloadURL  https://<site>/userscript/traderie-tools.user.js
// @updateURL    https://<site>/userscript/traderie-tools.meta.js
```

Userscript feed URLs should point to the published JSON:

- Preferred: `https://<site>/data/traderie_tools_prices.json`
- Legacy fallback: `https://<site>/data/rune_prices_legacy.json`

### Release checks

- Userscript installs in Tampermonkey from the public URL.
- Userscript fetches the public JSON URL without CORS issues.
- Userscript defaults to `pc_sc_nl` only with a visible caveat.
- Userscript never reads or displays cash prices for deal evaluation.
- Userscript shows low-confidence/unavailable states instead of falling back across segments.

## 6. Add Alerting

### What to alert on

Alert on conditions that affect the daily public feed:

- Snapshot launchd job exits nonzero.
- Regeneration launchd job exits nonzero.
- Any segment's latest snapshot is older than the expected schedule plus grace period.
- Product JSON is older than 30 hours.
- Validator failure for in-game or cash products.
- Published site/feed timestamp does not match latest product timestamp.

### Recommended mechanism

Keep it simple: add one local alert script that runs after regeneration and sends a macOS notification plus writes a concise alert log.

Initial mechanism:

- `scripts/collection_status.py --json` as the source of truth.
- Local notification via `osascript -e 'display notification ...'`.
- Alert log under `logs/launchd/alerts.log`.
- Exit nonzero when status is bad so launchd stderr captures it.

Why local notification first:

- The pipeline is currently local launchd-based.
- It avoids GitHub Actions complexity while Traderie Cloudflare/API behavior remains local-machine dependent.
- It can later be replaced or supplemented with GitHub Actions once site publishing is automated.

### Alert thresholds

- Snapshot stale warning: latest normalized snapshot mtime older than 8 hours.
- Segment stale warning: latest observed trade older than 24 hours, except thin hardcore can be warning rather than fatal if the snapshot itself is fresh.
- Product stale fatal: `product_generated_at` older than 30 hours.
- Regeneration fatal: any validator exits nonzero.

## 7. Priority-Ordered Build Plan

### Phase 1: Fix pipeline, get exit 0

| Task | Dependency | Estimate | Risk |
|---|---|---:|---|
| Inspect current launchd state and confirm current runner path | None | 0.25 day | Low |
| Probe recent hardcore failures by item/segment | Network availability | 0.5 day | Medium |
| Define and implement skip/quarantine policy for persistent hardcore item failures | Probe results | 0.5-1 day | Medium |
| Adjust success/failure semantics so known item misses do not fail the whole job, but infrastructure failures still do | Skip/quarantine policy | 0.5 day | Medium |
| Run two consecutive clean snapshot cycles | Code changes complete | 0.5-1 day elapsed | Medium |

Exit criteria:

- Snapshot job exits 0 for expected known conditions.
- `collection_status.py --json` reports fresh snapshots for all four segments.
- Known hardcore gaps are visible in status, not hidden.

### Phase 2: Load regen plist, verify

| Task | Dependency | Estimate | Risk |
|---|---|---:|---|
| Validate `scripts/regenerate_products.sh` and regeneration plist | Phase 1 stable enough to produce useful history | 0.25 day | Low |
| Run manual regeneration and validators | Fresh snapshot/history | 0.25 day | Low |
| With Buddy approval, copy and bootstrap regenerate plist | Manual run passes | 0.25 day | Low |
| Verify next scheduled 06:00 run updates products | Loaded plist | 1 day elapsed | Low |

Exit criteria:

- Product JSON is regenerated daily.
- Product timestamps are less than 30 hours old.
- Validators pass after scheduled regeneration.

### Phase 3: Publish site + userscript

| Task | Dependency | Estimate | Risk |
|---|---|---:|---|
| Build web app with fresh data | Phase 2 | 0.25 day | Low |
| Fix public methodology/userscript wording drift | Phase 2 | 0.25 day | Low |
| Add site download section for userscript and feeds | Hosting decision | 0.5 day | Medium |
| Configure GitHub Pages static publish allowlist | Hosting decision | 0.5 day | Medium |
| Smoke-test published site and feed URLs | Publish workflow | 0.25 day | Medium |

Exit criteria:

- Public site loads without local filesystem assumptions.
- Rune prices, confidence, volume, freshness, and segment selector work.
- Downloadable userscript URL works.
- Userscript fetches public JSON successfully.

### Phase 4: Add alerting

| Task | Dependency | Estimate | Risk |
|---|---|---:|---|
| Add local alert script around `collection_status.py --json` | Phase 2 | 0.5 day | Low |
| Wire alert script after regeneration | Alert script | 0.25 day | Low |
| Add stale product/site feed check | Published URLs | 0.25-0.5 day | Medium |
| Document response runbook | Alert behavior finalized | 0.25 day | Low |

Exit criteria:

- Buddy gets one clear notification when daily pipeline or product freshness fails.
- Alert includes failing area: snapshot, regeneration, validation, stale product, or publish mismatch.

## 8. Open Decisions for Buddy

| Decision | Options | Recommendation |
|---|---|---|
| Hosting/domain | GitHub Pages under repo/org, custom domain, or another static host | Start with GitHub Pages; add custom domain later if needed. |
| Public data scope | In-game only; in-game plus cash comparison; include source directory | Publish in-game values, source directory, methodology, and userscript feed. Publish cash comparison only if labels are strong and no raw artifacts are exposed. |
| Userscript distribution | Link to external repo only; host downloadable copy; embed script text on site | Host downloadable `.user.js` on the price site and link back to external repo as source. |
| Hardcore gap policy | Fail on any item miss; skip persistent failures; quarantine/report failures; remove unsupported items | Quarantine/report persistent failures and allow clean exits when coverage thresholds are met. |
| Regeneration ownership | Local launchd only; GitHub Actions; hybrid | Use local launchd for Traderie collection/regeneration now; consider GitHub Actions only for static publish after JSON is generated. |
| Cash prices on public site | Hide; show comparison-only; show source directory only | Show comparison-only only if separated from in-game values and labeled `use_in_model=false`. |

## Next Step Recommendation

Buddy should authorize a worker to fix the hardcore snapshot failure policy first: inspect the current launchd state, probe the recurring `pc_hc_l` and `pc_hc_nl` timeout items, and implement a visible skip/quarantine path so the scheduled snapshot job can exit 0 for expected thin-economy failures while still failing on real infrastructure problems.
