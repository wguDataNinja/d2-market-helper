# Static UI Scaffold

Date: 2026-06-20

## Stack

- Vite 8 + React 19 + TypeScript
- react-router-dom for routing
- No backend. No live scraping. No external network calls.

## Pages

| Route | File | Purpose |
|---|---|---|
| `/` | `src/pages/Home.tsx` | Market overview: segment selector, snapshot cards, top runes, cash comparison, source directory |
| `/runes` | `src/pages/Runes.tsx` | Full rune dashboard: 33 rune table bid/ask/confidence, cash column, sortable |
| `/sources` | `src/pages/Sources.tsx` | Source directory: every manifest entry with status, evidence, caveats |
| `/about-methodology` | `src/pages/Methodology.tsx` | Full methodology explanation with all caveats |

## Data Sources

All consumed via Vite's JSON imports from the project `data/` directory:

- `data/products/in_game_rune_values.json` — Traderie rune VWAP by segment
- `data/products/traderie_tools_prices.json` — Userscript-compatible feed
- `data/products/external_cash_prices.sample.json` — IGGM cash prices
- `data/source_manifest.json` — 20-source ledger
- `data/rune_registry.json` — 33-rune canonical ordering

## Key Design Rules

- Default segment: `pc_sc_nl` (PC Softcore Non-Ladder)
- Segment via URL query param: `?segment=pc_sc_nl`
- No cash/in-game blending (separate visual columns)
- Cash prices: "external comparison only" disclaimer on every page
- Source + confidence visible near every number
- Unavailable/thin-volume states shown (not hidden)
- Methodology page explains every rule

## How to Run

```bash
cd web
npm install     # already done
npm run dev     # dev server at http://localhost:5173
npm run build   # production build to web/dist/
```

## Build Status

TypeScript check: ✅ passed (0 errors)
Vite build: ✅ passed (597 KB JS + 7 KB CSS, ~100 KB gzip)

## Files Created/Changed

| File | Action |
|---|---|
| `web/src/data/types.ts` | Fixed `RuneObservation` field names (`bid_ct`→`bid_count`, `ask_ct`→`ask_count`, `trade_count`→`total_trades`), fixed `InGameRuneValues` to wrap in `segments` object, fixed `CashObservation` (`source`→`source_slug`, removed `segment`, added direct platform/ladder fields), removed `ExternalCashPrices.metadata` (not in JSON) |
| `web/src/data/loader.ts` | Fixed `getSegmentData` to access `segments[segment].runes` instead of top-level key; added `getCashPricesForRune` helper |
| `web/src/pages/Home.tsx` | Updated field refs: `trade_count`→`total_trades`, `obs.source`→`obs.source_slug` |
| `web/src/pages/Runes.tsx` | Updated field refs: `trade_count`→`total_trades`, cash source uses `source_slug` dynamically |

All other files (Layout, SegmentSelector, ConfidenceBadge, StatusBadge, CashDisclaimer, Sources, Methodology, App.css, vite.config.ts, tsconfig.app.json) — unchanged from original scaffold.
