# Item Profiles

## Purpose

Item profiles are machine-readable item metadata. They are **not price outputs**. They describe an item's economic role, gameplay context, trading patterns, source data quality, and modeling risks.

Profiles guide:
- **Source discovery** — where to look for pricing or sentiment data
- **Pricing model design** — what model variants apply, what units to use
- **Website display** — whether an item appears on the website and how
- **Userscript warnings** — whether tooltips show price, confidence, or disclaimers
- **Research prioritization** — which items to focus Reddit/source research on

## Schema

### Top Level

```json
{
  "schema_version": "0.1",
  "item_id": "ist_rune",
  "display_name": "Ist Rune",
  "category": "runes",
  "game": "diablo2resurrected",

  "trade_relevance": { ... },
  "gameplay_context": { ... },
  "pricing_context": { ... },
  "source_signals": { ... },
  "research_notes": [ ... ],
  "open_questions": [ ... ],
  "last_reviewed_at": null,
  "confidence": "draft"
}
```

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | yes | Profile schema version |
| `item_id` | string | yes | Canonical slug (snake_case) |
| `display_name` | string | yes | Human-readable name |
| `category` | string | yes | One of: runes, commodities, uniques, charms, bases, runewords, sets, jewels, gems, misc |
| `game` | string | yes | Always `diablo2resurrected` |
| `trade_relevance` | object | yes | Market role and risk profile |
| `gameplay_context` | object | yes | What the item is used for in-game |
| `pricing_context` | object | yes | How the item is priced and traded |
| `source_signals` | object | yes | Source-by-source data quality assessment |
| `research_notes` | array | yes | Timestamped notes from research |
| `open_questions` | array | no | Unresolved questions about this item |
| `last_reviewed_at` | string or null | no | ISO date of last review |
| `confidence` | string | yes | draft, validated, mature, archived |

### trade_relevance

| Field | Type | Required | Values |
|---|---|---|---|
| `market_role` | string | yes | currency, commodity, sought_unique, chase_unique, common_unique, crafting_base, charm, key, token, consumable, vanity, low_trade |
| `liquidity` | string | yes | very_high, high, medium, low, very_low, unknown |
| `volatility` | string | yes | very_high, high, medium, low, very_low, unknown |
| `new_player_risk` | string | yes | high, medium, low, unknown |
| `commonly_used_as_currency` | boolean | yes | Whether this item is used as a de facto currency |

### gameplay_context

| Field | Type | Required | Description |
|---|---|---|---|
| `uses` | array of strings | yes | In-game uses (e.g. "runeword base", "respec token") |
| `demand_drivers` | array of strings | yes | What drives demand (e.g. "caster builds", "melee builds", "ladder reset") |
| `supply_notes` | array of strings | no | How supply enters the economy |

### pricing_context

| Field | Type | Required | Description |
|---|---|---|---|
| `common_quote_units` | array of strings | yes | What units prices are quoted in (e.g. "Ist Rune", "FG") |
| `common_trade_forms` | array of strings | yes | How the item is listed (e.g. "single item", "stack of 10") |
| `important_rolls_or_variants` | array of strings | no | Rolls that affect value |
| `segment_sensitivity` | array of strings | no | Segments where pricing differs (e.g. "ladder vs non-ladder", "softcore vs hardcore") |
| `known_model_risks` | array of strings | yes | Risks in modeling price for this item |

### source_signals

Each source:

| Field | Type | Required | Values |
|---|---|---|---|
| `use_for_pricing` | string | yes | yes, no, research_only, unknown |
| `notes` | string | no | Free-text notes about this source for this item |

Sources: `traderie`, `diablo2_io`, `reddit`, `d2jsp`, `rmt_sites`

### research_notes

Each entry:

| Field | Type | Required | Description |
|---|---|---|---|
| `date` | string | yes | ISO date |
| `source` | string | yes | manual, reddit, agent, d2jsp, discord, api_analysis |
| `note` | string | yes | Free-text observation |

## Directory Layout

```
data/item_profiles/
├── runes/           # Rune items
├── commodities/     # Keys, tokens, essences, organs
├── uniques/         # Unique items (weapons, armor, jewelry)
├── charms/          # Annihilus, Torch, skillers, small/large charms
├── bases/           # Runeword bases (armor, weapons, shields)
├── runewords/       # Completed runewords
└── (future) sets/   # Set items
```

## Confidence Levels

| Level | Meaning |
|---|---|
| `draft` | Initial sketch, needs market validation |
| `validated` | Reviewed against current market data |
| `mature` | Stable profile, minor updates only |
| `archived` | No longer relevant to current ladder/economy |

## Usage

Profiles are consumed by:
- **Pipeline scripts** — to decide which items to fetch, how to model them
- **Website** — to decide display treatment and disclaimers
- **Reddit research agents** — to know which items to watch for
- **Validation scripts** — to ensure profiles stay complete and correct

Profile data does not directly set prices. Price comes from the pipeline. Profile provides context for interpreting and using that price.
