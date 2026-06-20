# Source: Traderie

## URL

https://traderie.com/diablo-2-resurrected/trade

## Type

Player-to-player trade platform (primary pricing source for the pipeline).

## Rune Prices

Not visible in static HTML. The Traderie page is a fully dynamic React application. All content (listings, prices) loads via API calls after page render.

## Static vs Dynamic

Fully dynamic. The 7 KB downloaded HTML is just a React shell.

## Recommendation

**Structured pricing source (API).** Traderie is already the pipeline's primary source via the completed trades API endpoint. The web page itself is not useful for scraping — the API is the correct interface.

The pipeline currently uses:
```
https://traderie.com/api/diablo2resurrected/listings?completed=true&auction=false&prop_Platform=PC&...
```

## Next Steps

No additional downloads needed. The existing API integration already covers Traderie's structured trade data.
