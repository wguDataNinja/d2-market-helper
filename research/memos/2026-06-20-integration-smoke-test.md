# Integration Smoke Test

Date: 2026-06-20

## Commands Run

| Command | Result |
|---|---|
| `validate_source_manifest.py` | ✅ 20 sources valid |
| `validate_external_cash_prices.py` | ✅ 271 obs, 4 sources, schema v0.2 |
| `validate_in_game_rune_values.py` | ✅ Both in-game and traderie_tools products |
| `parse_itemnow_api.py` | ✅ 42 products (33 runes, 9 bundles), snapshot+history |
| `parse_d2stock_rss.py` | ✅ 199 observations (66 rune singles, 133 bundles) |
| `generate_external_cash_prices.py` | ✅ 271 observations merged (IGGM 30 + ItemNow 42 + items7 0 + D2Stock 199) |
| `generate_prices_json.py` | ✅ 4 segments, 92 rune observations, 2,570 modeled trades |
| `snapshot_traderie.py --segment pc_sc_nl --item "Jah Rune"` | ✅ 50 listings, 50 unique IDs, ~6.6h window |
| `cd web && npx vite build` | ✅ 0 tsc errors, build 99KB JS gzip |

Note: `snapshot_traderie.py` requires `.venv/bin/python` (has cloudscraper). System `python3` does not.

## Issues Fixed During Test

1. **Diablo2.io artifact paths stale.** Old `jah_sold_search/` path removed; replaced with four `_p1` paths (Jah, Ber, Lo, Sur).
2. **Snapshots/history not gitignored.** Added `data/snapshots/` and `data/history/` to `.gitignore`.

## Non-deterministic Outputs

- `data/products/external_cash_prices.sample.json` — cash prices change (ItemNow has price ranges, D2Stock feed may update). Will differ each run.
- `data/external/itemnow_cash_prices.json` — same, live-fetched.
- `data/external/d2stock_cash_prices.json` — same, live-fetched.
- `data/products/in_game_rune_values.json` — snapshot-dependent; Traderie rolling window means content shifts each poll.
- `data/snapshots/raw/*` — timestamps differ each run.
- `data/history/*.jsonl` — appended each run, never removed.

Deterministic with `--offline`/fixture flags: parse scripts respect offline mode.

## Gitignore Coverage

| Path | Ignored? | Should commit? |
|---|---|---|
| `data/raw/` | ✅ Yes | No — private intermediate data |
| `data/extracted/` | ✅ Yes | No — private intermediate data |
| `data/snapshots/` | ✅ Yes (now) | No — private raw captures |
| `data/history/` | ✅ Yes (now) | No — append-only, grows unbounded |
| `data/external/*.json` | ❌ No | Yes — canonical cash parser outputs |
| `data/products/*.json` | ❌ No | Yes — canonical public products |
| `data/research/` | ❌ No | Yes — research findings |
| `web/dist/` | ❌ No | No — build artifact |
| `*.har` | ✅ Yes | No — may contain session data |

## Files Changed (since init)

**Modified (12):**
- `.gitignore` — added snapshot/history exclusion
- `data/source_manifest.json` — Diablo2.io artifacts fixed, rankings updated
- `data/products/external_cash_prices.sample.json` — regenerated (271 obs)
- `scripts/fetch_completed_trades.py` — audit fields retained
- `scripts/extract_rune_trades.py` — audit fields propagated
- `scripts/generate_external_cash_prices.py` — multi-source merge
- `scripts/validate_external_cash_prices.py` — hardened schema
- `docs/DATA_PRODUCTS.md` — freshness labels, schema v0.2
- `docs/PRICING_MODEL.md` — source window subsection
- `docs/PROJECT_MEMORY.md` — session history
- `docs/SOURCE_MANIFEST.md` — surface checklist
- `research/memos/2026-06-20-source-discovery-workflow.md` — classification rule

**Untracked (new files, ~40+):** web/ scaffold, all research memos, scripts, research JSON files, fixtures, runbook.

## Recommended Commit Grouping

### Commit 1: Process correction + source discovery audit
- docs/SOURCE_MANIFEST.md
- research/memos/2026-06-20-source-discovery-workflow.md
- research/memos/2026-06-20-source-ranking-repair.md
- research/memos/2026-06-20-market-source-inventory-audit.md
- research/memos/2026-06-20-market-source-discovery-protocol.md
- research/memos/2026-06-20-d2r-market-source-candidate-map.md
- data/source_manifest.json

### Commit 2: Traderie pipeline hardening + snapshot infrastructure
- scripts/fetch_completed_trades.py
- scripts/extract_rune_trades.py
- scripts/snapshot_traderie.py
- scripts/lib/snapshot_io.py
- research/memos/2026-06-20-traderie-raw-response-audit.md
- research/memos/2026-06-20-traderie-normalized-audit-fields.md
- research/memos/2026-06-20-traderie-pagination-window-audit.md
- research/memos/2026-06-20-traderie-snapshot-collector.md
- research/memos/2026-06-20-snapshot-history-plan.md
- docs/COLLECTION_RUNBOOK.md
- research/memos/2026-06-20-collection-scheduler-plan.md
- .gitignore

### Commit 3: Cash parsers + external cash product
- scripts/parse_itemnow_api.py
- scripts/parse_d2stock_rss.py
- scripts/generate_external_cash_prices.py
- scripts/validate_external_cash_prices.py
- data/external/itemnow_cash_prices.json
- data/external/d2stock_cash_prices.json
- data/products/external_cash_prices.sample.json
- data/rune_registry.json
- research/memos/2026-06-20-itemnow-api-probe.md
- research/memos/2026-06-20-itemnow-cash-parser.md
- research/memos/2026-06-20-d2stock-rss-parser.md
- research/memos/2026-06-20-external-cash-product-contract.md
- research/memos/2026-06-20-product-freshness-labels.md
- docx/DATA_PRODUCTS.md
- docx/PRICING_MODEL.md

### Commit 4: Diablo2.io research
- research/sources/diablo2_io.md
- research/memos/2026-06-20-process-correction-diablo2io.md
- research/memos/2026-06-20-diablo2io-parser-validation-plan.md
- research/memos/2026-06-20-diablo2io-sold-search-fixture.md
- research/memos/2026-06-20-diablo2io-ber-sold-search-fixture.md
- research/memos/2026-06-20-diablo2io-fixture-pack.md
- research/memos/2026-06-20-diablo2io-semantic-validation-report.md
- research/memos/2026-06-20-diablo2io-diagnostic-readiness.md
- research/memos/2026-06-20-traderie-diablo2io-comparison-design.md
- scripts/parse_diablo2io_sold_search_offline.py
- data/research/diablo2io_sold_*.json
- research/sources/captures/diablo2io/*/rendered.html

### Commit 5: Probe results
- research/memos/2026-06-20-playerauctions-rune-specific-probe.md
- research/memos/2026-06-20-player-community-source-probes.md
- research/memos/2026-06-20-zero-artifact-cash-source-probes.md
- research/sources/captures/playerauctions/
- research/sources/captures/eldorado/
- research/sources/captures/mmopixel/
- research/sources/captures/mulefactory/
- research/sources/captures/rpgstash/
- research/sources/captures/d2stock/
- research/sources/captures/reddit/

### Commit 6: UI scaffold
- web/ (everything except dist/)

### Single commit alternative
`git add --all` with message: "feat: multi-source market intelligence hub — Traderie hardened pipeline, 4 cash parsers (271 obs), Diablo2.io research (14 candidate rows), source discovery protocol, snapshot infrastructure, and static UI scaffold"
