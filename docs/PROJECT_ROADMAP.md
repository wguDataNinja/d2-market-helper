# D2R Market Helper — Project Roadmap

## Product Vision

D2R Market Helper is a coordinated set of tools that helps Diablo II: Resurrected players understand item values, find trade venues, and compare prices across sources.

### Components

| Component | Purpose | Status |
|---|---|---|
| **Rune price pipeline** | Fetch completed trades from Traderie API, extract rune-for-rune trades, compute Ist-normalized VWAP | Active (3 scripts) |
| **Streamlit dashboard** | Browse live trades by segment, filter by rune, export to CSV | Active (`app.py`) |
| **Traderie Tools userscript** | Tampermonkey script overlaying rune prices on Traderie listings | External repo (`wguDataNinja/TraderieTools`) |
| **Item registry** | Canonical item list with aliases, categories, and source IDs | Created (1,328 items) |
| **Item profiles** | Economic metadata per item — role, liquidity, risks, source quality | Started (12 profiles) |
| **Market research** | Reddit pass completed, source discovery started | Phase 1 complete |
| **Source directory** | Catalog of trade/pricing sources with evidence ratings | Started (10 sources documented) |

### Questions the project answers

- Where are D2R trades happening?
- What are runes worth in my segment?
- Which sites have visible cash prices?
- How do cash prices differ from in-game trade ratios?
- Which items are worth tracking later?
- Which sources are trustworthy for which purpose?

## Phases

### Phase 1 — Stabilize Pipeline (Now)

- Run pipeline deterministically
- Add schema-versioned public JSON output
- Add validation step after each stage
- Document output schemas

### Phase 2 — Website Prototype

- Source directory page
- Rune price table by segment
- Item/source watchlist
- Clear evidence labels on all prices

### Phase 3 — External Cash-Price Comparison

- Offline parsers for saved PlayerAuctions/items7 HTML
- Normalized `external_cash_prices` schema
- Website display flagged as "cash listing price — not in-game trade value"
- No blending into in-game rune model

### Phase 4 — Source Discovery Expansion

- Investigate diablo2.io
- Investigate d2jsp forum price-check threads
- Investigate Discord / Baal's Ledger as venue
- Map platform filters and completed-trade surfaces

### Phase 5 — Userscript Integration

- Consume stable `in_game_rune_values.json`
- Show fair-value estimates with confidence
- No cash-price data in userscript initially

## Invariants

- Never merge segments. PC softcore ladder is a separate economy from PC softcore non-ladder.
- Never blend cash/RMT prices into the in-game rune value model. Cash prices are comparison-only.
- Every price observation must carry segment metadata (platform, mode, ladder, hardcore).
- Missing segment metadata lowers confidence or excludes the observation.
- Reddit/community mentions are qualitative only — not pricing data.
- Active listings are not completed trades.
- Public-facing data must be schema-versioned.
