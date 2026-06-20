# Item Registry

## Purpose

The item registry is a machine-readable reference layer that maps all known Diablo II: Resurrected items to canonical identifiers, aliases, categories, and source IDs. It is the authoritative source for item identity across the project — used by the pricing pipeline, Reddit extraction, item profiles, and the website.

The registry answers:
- What is this item called in Traderie, Reddit, d2jsp, and game data?
- What category does this item belong to?
- Does this item have a profile with economic context?
- What aliases or shorthand names are used for this item?

## Registry Files

```
data/item_registry/
├── items.json              # Canonical item list (1 per item)
├── aliases.json            # Common name mappings
├── categories.json         # Category taxonomy with counts
├── extraction_rules.json   # Matcher patterns for Reddit extraction
└── (future) candidates.jsonl  # Unresolved terms needing review
```

### items.json

List of canonical items. Each entry:

```json
{
  "item_id": "ist_rune",
  "canonical_name": "Ist Rune",
  "category": "runes",
  "trade_groups": ["mid_runes"],
  "source_ids": {
    "traderie": 2290642411,
    "traderie_catalogue_id": 2290642411
  },
  "aliases": [],
  "profile_path": "data/item_profiles/runes/ist.json",
  "in_catalogue": true
}
```

| Field | Type | Description |
|---|---|---|
| `item_id` | string | Canonical slug (snake_case, used across project) |
| `canonical_name` | string | Full game name |
| `category` | string | One of the registry categories |
| `trade_groups` | array | Economic grouping tags (currency_runes, mid_runes, low_runes, keys, perfect_gems) |
| `source_ids.traderie` | int | Traderie API item ID (pipeline fetch list) |
| `source_ids.traderie_catalogue_id` | int | Traderie.com catalogue item ID (1328-item catalogue) |
| `aliases` | array | Known shorthand names linked from aliases.json |
| `profile_path` | string or null | Path to item profile if one exists |
| `in_catalogue` | bool | Whether this item appears in the full Traderie catalogue |

### aliases.json

Common name mappings. Each entry:

```json
{
  "alias": "Shako",
  "canonical_name": "Harlequin Crest",
  "item_id": "harlequin_crest",
  "confidence": "high",
  "context": "unique diadem",
  "canonical_item": {
    "item_id": "harlequin_crest",
    "canonical_name": "Harlequin Crest"
  }
}
```

| Field | Type | Description |
|---|---|---|
| `alias` | string | Shorthand name as written by players |
| `canonical_name` | string | Full item name |
| `item_id` | string or null | Canonical item_id. null for generic terms (HR, 3x3, PGem) |
| `confidence` | string | high, medium, low — how established this alias is |
| `context` | string | Explanation of what this alias refers to |
| `canonical_item` | object or null | Resolved item reference if item_id exists in registry |
| `resolution_status` | string | needs_review if item_id not found in registry |

### categories.json

```json
{
  "category": "runes",
  "item_count": 33,
  "profile_count": 3,
  "description": "33 rune items used in runewords and as trade currency"
}
```

### extraction_rules.json

Matcher patterns for automated text extraction. Separates deterministic matches from context-dependent or ambiguous terms.

```json
{
  "short_rune_names": ["el", "eld", "eth", "io", "ith", ...],
  "matcher_patterns": [
    {
      "item_id": "ist_rune",
      "patterns": ["ist rune"],
      "category": "runes",
      "requires_word_boundary": false
    }
  ],
  "unresolved_rules": {
    "word_boundary_context": ["El Rune", "Eld Rune", ...],
    "context_dependent": ["3x3", "HR", "PGem", "Torch"],
    "do_not_match_within_words": ["Lo in 'lol', 'loot'", "El in 'help', 'level'"]
  }
}
```

## Categories

| Category | Items | Description |
|---|---|---|
| runes | 33 | All runes including rune words |
| uncategorized | 1247 | Items needing classification — bases, armors, weapons, sets |
| commodities | 16 | Keys, essences, tokens, organs |
| jewelry | 19 | Rings, amulets, circlets |
| gems | 7 | Perfect gems |
| charms | 3 | Small, large, grand charms + unique charms |
| bases | 1 | Runeword base items |
| jewels | 1 | Jewels |
| uniques | 1 | Unique items |

> Note: 1247 items are uncategorized because the Traderie catalogue includes every game item variant (base items, normal/exceptional/elite tiers, class-specific items). Classification is ongoing.

## Source Priority

When resolving an item name from text:

1. **Exact match** against `items.json` canonical names (word-boundary checked)
2. **Alias match** against `aliases.json` (word-boundary required)
3. **Short rune check** — single-word rune names (El, Io, Lo) require word boundaries and context (e.g. "Lo Rune" vs "loot")
4. **Unresolved** — terms that don't match go to `candidates.jsonl` for review

## LLM Use Policy

- LLM may propose aliases, item candidates, and profile notes
- LLM may not directly promote unresolved terms to canonical items without review
- LLM outputs should be marked draft/research until validated
- Add proposals to `research/reddit/notes/` with `(proposed)` prefix
- After human approval, add to registry aliases or create item profile

## Maintenance

- `items.json` is regenerated from source catalogue data when the catalogue changes
- `aliases.json` is curated — add new aliases as they surface from Reddit/d2jsp research
- `extraction_rules.json` is updated when new ambiguous terms are identified
- Unresolved terms are reviewed in batches during Reddit research cycles

## See Also

- `docs/ITEM_PROFILES.md` — Economic metadata per item
- `docs/REDDIT_RESEARCH_PLAN.md` — How Reddit research feeds the registry
- `data/item_profiles/` — Individual item profiles
- `scripts/validate_item_profiles.py` — Validates profiles against the registry schema
