# D2Stock RSS Parser — 2026-06-20

## Feed URL

`https://d2stock.com/rss.xml` — Google Shopping XML feed (2.2 MB, 2,014 items)

## Parse Approach

- XML parsing via `xml.etree.ElementTree` (stdlib, no deps)
- Filtered to product types under `Runes >` taxonomy
- Three subcategories: `Buy D2R Runes` (singles), `Rune Packs` (10× bundles), `Runewords` (runeword bundles)
- Rune names mapped via `data/rune_registry.json` for normalization and rune_order
- Segment extracted from title after `•` delimiter: `Softcore Ladder RotW` / `Softcore Non-Ladder RotW`
- `--offline` flag reads saved fixture at `research/sources/captures/d2stock/2026-06-20_search_probe/rss_feed.xml`

## Observation Count

| Category | Count |
|----------|-------|
| Single runes | 66 (33 runes × 2 segments) |
| 10-packs | 66 (33 runes × 2 segments) |
| Runeword bundles | 67 |
| **Total** | **199** |

## Rune Price Range

- Low runes (El–Hel): $0.35 flat across both segments
- Mid runes (Io–Gul): $0.33–$1.36 (segment-dependent for Um/Mal/Ist/Gul)
- High runes (Vex–Zod): $1.14–$9.94 (segment-dependent for Vex/Sur/Ber/Jah/Cham/Zod)
- 10-pack pricing: slight discount vs 10× single price (e.g., Ladder: $3.35 vs $3.50 for El)

## Segment Findings

- Two segments detected in titles: `Softcore Ladder RotW`, `Softcore Non-Ladder RotW`
- No Hardcore or LoD items found in runes category
- Segment-specific pricing confirmed (e.g., Ber Rune: $7.94 Ladder vs $6.84 Non-Ladder)
- Same product URL used for both segments (no per-segment deep links)
- `segment_confidence: "low"` — segments are in titles but cannot verify store filter behavior

## Caveats

- Prices are asking prices, not completed sales
- All items listed as "in stock" — no out-of-stock items observed to verify feed reliability
- Feed captured 2026-06-20; prices may have changed
- Same product URL shared across segments — cannot deep-link to segment-specific page
- No Hardcore segment items found; may not be sold, or may use different product type
- 10-pack and runeword bundle items categorized as `bundle` — excluded from single-rune price comparisons
- RSS feed at `/rss.xml` is Cloudflare-proxied but accessible via curl with proper User-Agent
- Runeword count (67) is odd — one runeword may only exist in one segment

## Segment Limitations

- No platform info available from feed (likely PC by convention)
- No season/ruleset info
- `RotW` (Reign of the Warlock) in segment label suggests expansion-specific ruleset
- `base_price_scope: "unknown"` — prices are per-item and per-segment, but store may apply different pricing for other segments not in feed
