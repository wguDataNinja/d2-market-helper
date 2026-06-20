# Source: IGGM

## URL

https://www.iggm.com/d2-resurrected-items

## Type

Cash/RMT marketplace. JS-rendered product listings with extractable price attributes.

## Browser Capture Results

### Smoke Test (2026-06-20)
See `research/sources/captures/iggm_2026-06-20_browser-smoke/`

Page rendered. Rune prices visible in DOM via `lkr` attribute. 30 runes extracted. Segment context ambiguous from this capture (general D2R items page).

### Runes-Focused Capture (2026-06-20)
See `research/sources/captures/iggm_2026-06-20_runes-focused/`

Page rendered. Dedicated rune navigation found and followed. Segment filters identified in page text.

**Detected segment context:**
- Platform: PC
- Ladder: Non-Ladder
- Hardcore: No (Softcore)
- Season/Ruleset: ROTW (Reign of the Warlock)

Segment confidence: **high** — all dimensions detected from page content.

## Rune Prices

30 rune prices extracted via offline parser (`scripts/parse_iggm_offline.py`):

| Rune | Price |
|------|-------|
| Zod | $8.99 |
| Cham | $4.99 |
| Jah | $7.90 |
| Ber | $7.29 |
| Sur | $4.29 |
| Lo | $2.79 |
| Ohm | $1.79 |
| Vex | $0.89 |
| Gul | $0.39 |
| Ist | $0.49 |
| Mal | $0.29 |
| Um | $0.19 |
| Pul | $0.22 |
| Lem–Lum | $0.12 |
| Hel–Nef | $0.09 |

## Extraction Method

Parser uses regex to find `<p class="item-title">` for rune names and `<span class="price" lkr="...">` for numeric prices. Both elements appear sequentially in the DOM — matching by positional index is reliable.

## Assessment

**Suitable for:** External cash-price comparison. Parser prototype ready.

The IGGM parser is the first `parser_prototype_ready` source in the manifest. Prices are clean, rune coverage is complete (30/30), and segment context was confirmed from the focused capture.

## Caveats

- Prices are asking prices, not completed sales.
- Only one segment view was captured (PC, Non-Ladder, Softcore, ROTW). Other filter combinations may yield different prices.
- Dedicated runes page may have different prices than the general items page.

## Next Action

Verify prices against a different segment view (e.g. PC Ladder Hardcore) to test whether segment filters affect displayed prices.
