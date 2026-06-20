# Architecture

## Segment/Server Model

D2R economies are separate by platform, mode, ladder status, and hardcore state. The minimum viable model covers 4 PC segments:

| Slug | Platform | Mode | Ladder | Hardcore |
|---|---|---|---|---|
| `pc_sc_l` | PC | Softcore | Yes | No |
| `pc_sc_nl` | PC | Softcore | No | No |
| `pc_hc_l` | PC | Hardcore | Yes | Yes |
| `pc_hc_nl` | PC | Hardcore | No | Yes |

### Rules

- Never merge segments by default. Each segment is a separate economy.
- Every price observation must include segment/platform/mode/ladder/hardcore where available.
- Missing segment metadata lowers confidence or excludes the observation from segment-specific models.
- Other platforms (PlayStation, Xbox, Switch) are future discovery targets.
- Source discovery should document which segment filters each site exposes.

## Evidence/Source Classes

Clearly separated by data quality and intent:

### 1. `completed_player_trades`
- Best source for in-game relative rune values.
- Initial source: Traderie completed trades API.
- These are actual completed swaps between players — the closest thing to a market price.

### 2. `active_player_listings`
- Useful for market depth and asking prices.
- Weaker than completed trades — asking prices may not reflect actual transaction prices.
- Not used in the current model.

### 3. `forum_trade_posts`
- Example: d2jsp price-check threads, forum trade posts.
- Useful but represents a separate economy if Forum Gold (FG) is involved.
- FG-to-Ist conversion is an indirect reference, not a direct comparison.

### 4. `cash_market_listings`
- RMT/cash site asking prices (PlayerAuctions, items7, Odealo, etc.).
- Useful for external comparison and shopping reference only.
- **Do not blend into the in-game relative rune model.**
- Cash prices may include padding from transaction fees, minimum price floors, and profit margins.

### 5. `community_discussion`
- Reddit, Discord, general forums.
- Qualitative only. Not pricing data.
- Used for: venue discovery, player language, item candidates, new-player pain points.

## Data Flow

```
Traderie API
    │
    ▼
fetch_completed_trades.py
    │ raw_trades_{segment}.json
    ▼
extract_rune_trades.py
    │ extracted_trades_{segment}.csv
    ▼
calculate_rune_prices.py
    │ rune_prices_{segment}.csv
    ▼
consolidate_prices.py (planned)
    │ rune_prices_consolidated.csv
    ▼
generate_prices_json.py (planned)
    │ in_game_rune_values.json  ───→ Website
                                  ───→ Userscript
                                  ───→ External consumers

External sources (PlayerAuctions, items7, etc.)
    │
    ▼
Offline parsers (planned)
    │ external_cash_prices.json  ───→ Website (comparison only)

Item registry + profiles
    │
    ▼
All consumers (matching, metadata, disclaimers)
```

## Directory Layout

```
traderie/
├── app.py                          # Streamlit dashboard
├── server_configs.json             # 4 segment API configs
├── .gitignore                      # Raw data, research data, .env
├── data/
│   ├── item_ids.json               # Pipeline item fetch list
│   ├── traderie_catalogue.json     # Full catalogue (1,328 items)
│   ├── item_registry/              # Canonical items + aliases
│   │   ├── items.json
│   │   ├── aliases.json
│   │   ├── categories.json
│   │   └── extraction_rules.json
│   ├── item_profiles/              # Economic metadata per item
│   │   ├── runes/
│   │   ├── commodities/
│   │   ├── uniques/
│   │   ├── charms/
│   │   └── bases/
│   ├── raw/                        # Pipeline raw API output (gitignored)
│   ├── extracted/                  # Normalized trades (gitignored)
│   ├── prices/                     # Computed rune prices
│   └── .old/                       # Legacy data archive
├── scripts/
│   ├── fetch_completed_trades.py   # Step 1
│   ├── extract_rune_trades.py      # Step 2
│   ├── calculate_rune_prices.py    # Step 3
│   ├── validate_item_profiles.py   # Profile validation
│   └── reddit_extract_items.py     # Registry-based Reddit extraction
├── tools/
│   └── subreddit_research/         # Portable Reddit collection tool
├── research/
│   ├── reddit/                     # Raw posts, selected candidates, notes
│   ├── item_candidates/            # Proposed item profiles
│   ├── memos/                      # Per-pass learning documents
│   └── sources/                    # Per-source reports + downloads
├── pages/
│   └── trade_count.py              # Streamlit page
├── docs/
│   ├── MARKET_RESEARCH.md          # Research methodology
│   ├── SOURCE_DISCOVERY.md         # Source ratings and priority
│   ├── ITEM_REGISTRY.md            # Registry schema
│   ├── ITEM_PROFILES.md            # Profile schema
│   ├── REDDIT_RESEARCH_PLAN.md     # Reddit collection policy
│   ├── PROJECT_ROADMAP.md         # This file
│   ├── ARCHITECTURE.md            # This file
│   ├── PRICING_MODEL.md           # Pricing methodology
│   ├── DATA_PRODUCTS.md           # Output schemas
│   └── CODEX_HANDOFF.md           # Implementation guide
└── reports/                        # Legacy report scripts
```
