# Codex Handoff — D2R Market Helper

## Repo

`/Users/buddy/projects/traderie/`

Python 3.14, venv at `.venv/` with deps: pandas, numpy, streamlit, cloudscraper, tabulate, matplotlib, pytz, praw, python-dotenv.

## What Is Already Done

### Pipeline (Working)

| Script | Purpose | Status |
|---|---|---|
| `scripts/fetch_completed_trades.py` | Fetch Traderie API data for 4 PC segments | Working — 30K+ trades |
| `scripts/extract_rune_trades.py` | Extract rune-for-rune trades from raw JSON | Working |
| `scripts/calculate_rune_prices.py` | Compute Ist-normalized VWAP per segment | Working |
| `scripts/check_file_sizes.py` | Count trades in raw files | Working |
| `app.py` | Streamlit dashboard for trade browsing | Working |
| `server_configs.json` | 4 segment configs | Working |

### Data Layer (Created)

| Path | What |
|---|---|
| `data/item_registry/items.json` | 1,328 canonical items |
| `data/item_registry/aliases.json` | 35 alias mappings |
| `data/item_registry/categories.json` | 9 categories |
| `data/item_profiles/` | 12 draft profiles (runes, keys, charms, uniques, base) |

### Research (Complete)

| Area | Status |
|---|---|
| Reddit pass 1 (2,998 posts, 3 subreddits) | Closed. No comments fetched. |
| Source discovery — 10 sites inspected | Documented in `research/sources/*.md` |
| Item profiles — 12 draft | `data/item_profiles/` |
| Item registry — 1,328 items | `data/item_registry/` |

### Research Tools (Available)

| Tool | Path |
|---|---|
| Reddit collection tool | `tools/subreddit_research/` |
| Registry-based item extraction | `scripts/reddit_extract_items.py` |
| Profile validation | `scripts/validate_item_profiles.py` |

## What Is NOT Done (Ready for Codex)

### Phase 1 — Pipeline Stabilization

- [ ] `scripts/consolidate_prices.py` — Merge per-segment CSVs into one
- [ ] `scripts/generate_prices_json.py` — Produce schema-versioned `in_game_rune_values.json`
- [ ] Pipeline CLI — Single `python run_pipeline.py` command with `--segments` and `--env-file`
- [ ] Validation step — Check output after each stage, exit nonzero on failure
- [ ] Add `model_version` and `pipeline_version` to outputs

### Phase 2 — Website Prototype

- [ ] Source directory page (read from `source_directory.json`)
- [ ] Rune price table by segment (read from `in_game_rune_values.json`)
- [ ] Evidence labels on all displayed prices
- [ ] Item profile viewer page (read from `data/item_profiles/`)

### Phase 3 — External Cash-Price Comparison

- [ ] `scripts/parse_playerauctions.py` — Extract prices from saved `research/sources/downloads/rune_sources_2026-06-20/warlock_gear_sets.html`
- [ ] `scripts/parse_items7.py` — Extract per-rune prices from `items7.html`
- [ ] `data/external_cash_prices.json` schema and generation
- [ ] Website comparison display (flagged as cash, not in-game)

### Phase 4 — Source Discovery Expansion

- [ ] Investigate diablo2.io
- [ ] Investigate d2jsp price-check threads
- [ ] Map platform/segment filters for each source

### Phase 5 — Userscript Integration

- [ ] Publish stable `in_game_rune_values.json` to GitHub
- [ ] Update userscript to consume versioned JSON
- [ ] Add confidence/quality indicators to userscript tooltips

## Invariants (Do Not Violate)

1. **Never merge segments.** PC softcore ladder is a separate economy from PC softcore non-ladder.
2. **Never blend cash/RMT prices into the in-game rune model.** Cash prices are comparison-only.
3. **Every price observation must carry segment metadata.** Missing metadata lowers confidence.
4. **Reddit/community mentions are qualitative only.** Not pricing data.
5. **Active listings are not completed trades.** Asking prices are not transaction prices.
6. **Public-facing data must be schema-versioned.**
7. **Do not fetch comments or crawl live sites unless explicitly asked.**
8. **Do not implement live scrapers.** Offline parsers only.
9. **Preserve raw/private data ignores.** The `.gitignore` is set up correctly.
10. **The userscript consumes only stable public JSON.** No direct API calls from userscript.

## Open Questions

1. Should the pipeline and website live in the same repo or separate repos?
2. Should cash-price data be public or research-only?
3. Should the userscript show cash-price comparisons or only in-game values?
4. What is the update cadence for `in_game_rune_values.json`? (Manual → GitHub Action?)
5. Should segment-specific prices be merged into a blended "all segments" view? (Current answer: no.)
6. Is there a viable second source for completed trades besides Traderie?

## Files to Inspect First

| File | Why |
|---|---|
| `scripts/fetch_completed_trades.py` | Understand the fetch flow |
| `scripts/extract_rune_trades.py` | Understand extraction logic |
| `scripts/calculate_rune_prices.py` | Understand VWAP calculation |
| `docs/ARCHITECTURE.md` | Repo layout and data flow |
| `docs/PRICING_MODEL.md` | Model rules and constraints |
| `docs/DATA_PRODUCTS.md` | Planned output schemas |
| `docs/SOURCE_DISCOVERY.md` | Source ratings and priority |
| `docs/ITEM_REGISTRY.md` | Canonical item schema |
| `docs/ITEM_PROFILES.md` | Profile schema |
| `research/memos/2026-06-20-downloaded-site-discovery.md` | What was found in site inspection |
| `research/sources/playerauctions.md` | Best external source structure |

## Commands to Run

```bash
# Activate venv
cd /Users/buddy/projects/traderie && source .venv/bin/activate

# Validate item profiles
python scripts/validate_item_profiles.py

# Check pipeline works (dry run with no .env — will fail on creds, tests argparse)
python scripts/check_file_sizes.py

# Full pipeline (requires Reddit API .env for reddit tool, Traderie API needs scraper)
python scripts/fetch_completed_trades.py  # needs .env or --env-file
python scripts/extract_rune_trades.py
python scripts/calculate_rune_prices.py

# Streamlit dashboard
streamlit run app.py
```

## Validation Scripts

| Script | What It Validates |
|---|---|
| `scripts/validate_item_profiles.py` | All JSON files in `data/item_profiles/` |
| `scripts/check_file_sizes.py` | Raw trade data files exist and have content |
| `scripts/reddit_extract_items.py` | Registry-based item extraction (requires Reddit post data) |

## Opening Prompt (First Codex Task)

> You are joining the D2R Market Helper project as a research engineer. This is an open-ended source-discovery and architecture-review task, not just an implementation ticket.
>
> Read these docs first:
> - `docs/CODEX_HANDOFF.md`
> - `docs/PROJECT_ROADMAP.md`
> - `docs/ARCHITECTURE.md`
> - `docs/PRICING_MODEL.md`
> - `docs/DATA_PRODUCTS.md`
> - `docs/MARKET_RESEARCH.md`
> - `docs/SOURCE_DISCOVERY.md`
> - `docs/ITEM_REGISTRY.md`
> - `docs/ITEM_PROFILES.md`
>
> Then inspect:
> - `scripts/fetch_completed_trades.py`
> - `scripts/extract_rune_trades.py`
> - `scripts/calculate_rune_prices.py`
> - `data/item_ids.json`
> - `data/traderie_catalogue.json`
> - `research/sources/*.md`
> - `research/memos/2026-06-20-downloaded-site-discovery.md`
> - Downloaded site artifacts under `research/sources/downloads/`
>
> **Project goal:** Build a D2R Market Helper website and companion tools. The website should help players answer:
> - What are runes worth in my economy segment?
> - Where are D2R trades happening?
> - Which sites have usable current prices?
> - Which sites have the best real-money rune/item prices?
> - How do cash-site prices differ from in-game trade ratios?
> - Which source should be trusted for which kind of evidence?
> - Which selected high-value items should be tracked later?
>
> **Important modeling rules:**
> - D2R economies are segmented. Do not merge segments by default.
> - Minimum PC segments: `pc_sc_l`, `pc_sc_nl`, `pc_hc_l`, `pc_hc_nl`.
> - Traderie completed trades are currently the primary source for in-game relative rune ratios.
> - Cash/RMT sites are useful for external comparison only.
> - Do not blend real-money prices into the in-game rune ratio model.
> - Active listings are weaker evidence than completed trades.
> - Reddit/community data is qualitative only.
> - Runewords are mostly demand drivers for component runes, not primary price targets.
>
> **Your goals:**
> 1. Understand and document how the current Traderie completed-trade collection works.
>    - It uses Traderie's API `/listings` surface with `completed=true`.
>    - It fetches separately by segment/server and item.
>    - It is somewhat fragile/tricky because it depends on site/API behavior rather than an official public data product.
>    - Identify exactly what fields are available and which are used/ignored.
>    - Identify risks: Cloudflare, rate limits, pagination/window limits, dedupe, schema changes.
> 2. Inspect the downloaded source artifacts.
>    - Determine which sites expose rune prices in static HTML.
>    - Determine which sites expose structured data, embedded JSON, `data-bind` attributes, or endpoint clues.
>    - Determine which sites expose platform/ladder/hardcore/softcore filters.
>    - Determine which sites might support future collectors.
>    - Do not crawl live sites unless explicitly approved.
>    - Do not bypass login or anti-bot protections.
> 3. Prioritize source opportunities. Rank sources by usefulness: completed trades, active listings, forum reference, cash-market, qualitative only.
> 4. Recommend the next implementation path. Should we first: stabilize Traderie output JSON? Build offline parsers for PlayerAuctions/items7? Inspect Diablo2.io/d2jsp more deeply? Create website data schemas? Build a prototype homepage?
> 5. Produce a written report before making code changes.
>
> **Deliverables:**
> A. `research/memos/codex-source-discovery-review.md` including: current Traderie collection summary, source-by-source findings, source ranking, risks and blockers, best next opportunities, what not to pursue yet, recommended implementation sequence.
> B. Optional code only if low-risk: small offline parser prototypes for saved HTML only. No live crawlers, no new network fetches, no pricing model changes.
> C. Suggested next tasks: one immediate engineering task, one source-discovery task, one website/product task.
>
> **Do not:**
> - Merge segment data.
> - Blend cash/RMT prices into in-game rune values.
> - Implement live scrapers.
> - Fetch Reddit comments.
> - Create product claims from weak evidence.
>
> **After you produce your report:**
> If it agrees with the current direction, the first implementation task is probably:
> 1. Generate stable `in_game_rune_values.json` from existing Traderie pipeline.
> 2. Offline `external_cash_prices.json` prototype from PlayerAuctions/items7 saved HTML.
> 3. `source_directory.json` + prototype homepage data model.

## Docs to Read (in order)

1. `docs/PROJECT_ROADMAP.md` — Overall vision and phases
2. `docs/ARCHITECTURE.md` — Repo layout and data flow
3. `docs/PRICING_MODEL.md` — Model principles and constraints
4. `docs/DATA_PRODUCTS.md` — Planned output schemas
5. `docs/MARKET_RESEARCH.md` — Research methodology and phases
6. `docs/SOURCE_DISCOVERY.md` — Source ecosystem and ratings
7. `docs/ITEM_REGISTRY.md` — Canonical item matching layer
8. `docs/ITEM_PROFILES.md` — Economic metadata schema
