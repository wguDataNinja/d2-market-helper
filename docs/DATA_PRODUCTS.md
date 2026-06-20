# Data Products

## 1. `in_game_rune_values.json` (Planned)

**Purpose:** Public-facing rune prices by segment. Consumed by website and userscript.

**Status:** Not yet built. Requires `consolidate_prices.py` and `generate_prices_json.py`.

**Schema (proposed):**

```json
{
  "schema_version": "0.1",
  "generated_at": "2026-06-20T00:00:00Z",
  "pipeline_version": "1",
  "model": "ist_normalized_vwap_v1",
  "segments": {
    "pc_sc_l": {
      "segment": "pc_sc_l",
      "platform": "pc",
      "mode": "softcore",
      "ladder": true,
      "hardcore": false,
      "runes": {
        "Ber": {
          "value_ist": 17.25,
          "bid_price": 16.39,
          "ask_price": 18.12,
          "bid_count": 102,
          "ask_count": 118,
          "total_trades": 220,
          "confidence": "high"
        }
      }
    }
  },
  "metadata": {
    "trade_window": "2026-05-12 to 2026-06-20",
    "total_trades_analyzed": 30753,
    "notes": "Ist-normalized VWAP. Outlier filter: 0.5-50 Ists. AND trades excluded."
  }
}
```

**Confidence levels:** high (100+ trades), medium (20-99), low (5-19), very_low (1-4), insufficient (< 1).

## 2. `external_cash_prices.json` (Planned)

**Purpose:** Cash listing prices from RMT/marketplace sites. Comparison-only display.

**Status:** Active — IGGM parser (`scripts/parse_iggm_offline.py`) produces 30 rune prices with segment context (PC, Non-Ladder, Softcore, ROTW). items7 requires browser capture.

**Schema (proposed):**

```json
{
  "schema_version": "0.1",
  "generated_at": "2026-06-20T00:00:00Z",
  "sources": {
    "playerauctions": {
      "source_name": "PlayerAuctions",
      "source_type": "cash_market_listings",
      "source_url": "https://www.playerauctions.com/diablo-2-resurrected-items/",
      "caveats": [
        "Cash listing prices. Not in-game trade values.",
        "May include transaction fees and seller margins.",
        "Prices are asking prices, not completed sales."
      ],
      "segments_available": ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"],
      "items": {
        "ber_rune": {
          "segment_prices": {
            "pc_sc_l": [
              {"price_usd": 2.85, "observed_at": "2026-06-20", "source_page": "runes"},
              {"price_usd": 2.50, "observed_at": "2026-06-20", "source_page": "listing_290440467"}
            ]
          }
        }
      }
    }
  }
}
```

## 3. `source_directory.json` (Planned)

**Purpose:** Registry of all known pricing/trade sources with metadata.

**Status:** Data collected in `docs/SOURCE_DISCOVERY.md` and `research/sources/*.md`.

**Schema (proposed):**

```json
{
  "schema_version": "0.1",
  "sources": [
    {
      "source_slug": "traderie_api",
      "name": "Traderie API",
      "url": "https://traderie.com/api/diablo2resurrected/listings",
      "evidence_class": "completed_player_trades",
      "rating": "production",
      "segments": ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"],
      "api_endpoint": "https://traderie.com/api/diablo2resurrected/listings",
      "is_dynamic": false,
      "caveats": [],
      "last_inspected": "2026-06-20"
    }
  ]
}
```

## 4. `data/item_registry/items.json` (Active)

**Purpose:** Canonical item list. Used across all components for item matching.

**Status:** Active. 1,328 items from Traderie catalogue.

**Format:** See `docs/ITEM_REGISTRY.md`.

## 5. Item Profiles (Active)

**Purpose:** Economic metadata per item. Guides modeling, display, and research decisions.

**Status:** 12 profiles created (draft). See `docs/ITEM_PROFILES.md`.

## 6. Community Signals (Planned)

**Purpose:** Qualitative findings from Reddit and other community sources.

**Status:** Markdown-only for now (see `research/memos/`). Future versions may use structured JSON for website display.

**Current format:** Markdown reports in `research/reddit/notes/` and `research/memos/`.

## Consumers

| Data Product | Website | Userscript | Internal Research |
|---|---|---|---|
| `in_game_rune_values.json` | Yes | Yes | — |
| `external_cash_prices.json` | Yes (comparison only) | No (initially) | Yes |
| `source_directory.json` | Yes | No | Yes |
| `item_registry/*.json` | Yes | Via lookup | Yes |
| Item profiles | No (internal) | No | Yes |
| Community signals | Markdown summaries | No | Yes |
