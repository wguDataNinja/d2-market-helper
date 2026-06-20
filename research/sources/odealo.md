# Source: Odealo

## URL

https://odealo.com/games/diablo-2-resurrected/marketplace/runes

## Type

Cash/RMT marketplace. Static HTML shell with React-rendered prices. Product listing data is loaded dynamically via internal API.

## Rune Prices

Not directly visible in downloaded HTML. The page contains a JSON-LD AggregateOffer with 155 offers ranging $0.01–$999.00, but per-rune breakdowns are loaded by the React app.

## Selected Item Prices

Not visible. Only rune category page was downloaded — item-specific pages needed.

## Static vs Dynamic

Dynamic (React app). Prices are fetched from an internal API after page load.

## Segmentation

Excellent. Download shows structured segment data:
- `pc ladder`, `pc non-ladder`, `xbox ladder`, `switch non-ladder`, `ps hardcore non-ladder`
- `s14` (Season 14) and `rotw` (Reign of the Warlock) filters
- Items listed as `(s14)pc ladder softcore rotw jah - #31` — fully qualified segment paths

## API Clues

- No direct API endpoints visible in static HTML
- Google reCAPTCHA present (bot protection)
- Static assets served from `static.odealo.com`

## Recommendation

**External cash-market comparison only.** Structured segment naming is useful for modeling segment-specific listings. Per-rune prices require either rendering the page with JS or finding the internal API endpoint.

## Downloads Needed

- Individual listing pages for runes (to capture rendered prices)
- Item-specific pages for Annihilus, Torch, Griffon's Eye, SoJ
