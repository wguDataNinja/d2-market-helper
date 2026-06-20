# Source: PlayerAuctions

## URL

https://www.playerauctions.com/diablo-2-resurrected-items/
(downloaded via Warlock gear sets page)

## Type

Cash/RMT marketplace. Static HTML with inline listing data.

## Rune Prices

Visible structured listing data. Examples:
- `pc--rotw--ladder-s14--sc--runes--runes30-ber` — Ber rune on PC, ROTW, Ladder Season 14, Softcore
- `pc--rotw--ladder-s14--sc--runes--runes31-jah` — Jah rune, same segment
- `pc--rotw--ladder-s14--sc--runes--runes32-cham`
- `pc--rotw--ladder-s14--sc--runes--runes33-zod`
- `all-severs14-runes30-ber` — cross-platform Ber rune
- `ber-rune-hardcore-ladder-d2r` — hardcore ladder Ber

Price range visible: $27.54 to $1,999.00 (bundles).

## Selected Item Prices

Items visible in listing data:
- `rotw-s14-enigma-runeword-enigma-runes-only--jah-be` — Enigma runeset
- `rotw-s14-enigma-runeword-enigma-archon-plate-base` — Enigma base
- `rotwlod-s14-fortitude-runewords-fortitude-runes-on` — Fortitude
- `rotwlod-s14-infinity-runewords-infinity-runes-only` — Infinity
- `harlequin crest shako` — Shako item listing
- `wisp projector` — Wisp Projector ring

## Static vs Dynamic

Partially static. Listing summaries are server-rendered (visible in HTML `data-bind` attributes). Individual listing prices and details likely load dynamically via the PlayerAuctions API.

## Segmentation

Excellent. Listing data uses a structured path format:
- Platform: `pc`, `xbox`, `all-severs`
- Mode: `rotw`, `ladder-s14`, `hardcore-ladder`
- Type: `runes`, `runewords`, uniques by name
- Item: `runes30-ber`, `runes31-jah`, named items

## API Clues

Three API endpoints identified in page source:
- `https://user-api.playerauctions.com/`
- `https://public-api.playerauctions.com/`
- `https://account-api.playerauctions.com/`

## Recommendation

**External cash-market comparison only.** Structured listing data and segment naming are excellent for cross-referencing relative rune values against cash prices. The `data-bind` attribute pattern is parseable and contains slot/label/ID structure. Could potentially be used to build API-backed listing queries.

## Downloads Needed

- Search results for specific runes (to see price listing details)
- Individual listing pages to see full pricing and segment filter options
- Item-specific pages for selected uniques/charms
