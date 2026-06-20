# Source: YesGamers

## URL

https://www.yesgamers.com/diablo-2-resurrected

## Type

Cash/RMT marketplace. Large static HTML (884 KB) with JS-rendered pricing. Interactive filter UI for ladder/softcore/hardcore/ROTW.

## Rune Prices

27 rune types found in HTML text. Actual prices are loaded dynamically — no dollar amounts were extractable from the static HTML.

## Selected Item Prices

Annihilus, Hellfire Torch, Shako, and Harlequin Crest mentioned in page text.

## Static vs Dynamic

Dynamic. Prices require JS interaction. The filter UI (ladder toggle, softcore/hardcore toggle, ROTW toggle) suggests prices load via API calls.

## Segmentation

Interactive filter UI:
- Ladder / Non-ladder toggle
- Softcore / Hardcore toggle
- ROTW checkbox
- Platform selector visible in UI

## API Clues

- Static assets served from `static.yesgamers.com`
- No internal API endpoints visible in static HTML

## Recommendation

**External cash-market comparison only.** The segmentation UI is interesting (player-facing toggle for all four segment dimensions). Would need a browser session to see actual prices.

## Downloads Needed

- Page with JS-rendered prices (browser screenshot or HAR capture)
