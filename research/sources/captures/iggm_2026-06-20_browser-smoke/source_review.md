# IGGM — Browser Smoke Review

## 1. Did the page render?
Yes. Title: "Diablo 2 Resurrected Items For Sale, Buy D2R Items - IGGM". 11 listing cards found.

## 2. Were rune prices visible?
**Yes, clearly.** 10 price samples extracted. Per-rune prices visible:

| Rune | Price |
|------|-------|
| Zod (#33) | $8.99 |
| Cham (#32) | $4.99 |
| Jah (#31) | $7.90 |
| Ber (#30) | $7.29 |
| Sur (#29) | $4.29 |
| Lo (#28) | $2.79 |
| Ohm (#27) | $1.79 |

Runes appear to be listed with their in-game slot number (#33, #32, etc.) and clear "$X.XX" prices alongside Buy Now / Add To Cart buttons.

## 3. Were selected high-value item prices visible?
No — the page appears to be a general D2R items page, not a dedicated runes page. The rune listings at the top suggest runes are a primary category.

## 4. What segment filters exist?
Excellent: ladder, non-ladder, softcore, hardcore, season, rotw, pc, xbox, switch. These are visible in the page as toggle/selector options.

## 5. Are platform/ladder/hardcore/softcore/season visible?
All present. Platform: pc, xbox, switch. Mode: ladder/non-ladder, softcore/hardcore. Seasonal: rotw, season.

## 6. Is the site static, JS-rendered, embedded JSON, API-driven, or unclear?
Partially static. The category page loaded rune prices in the rendered DOM after JS hydration. Previous static capture had JSON-LD Product schema ($8.99 base price) but per-rune prices were not in the static HTML.

## 7. Could prices be parsed from rendered HTML?
**Yes.** Rune names, prices, and Buy Now buttons are in the rendered DOM. The structure is regular: `{RuneName} – #{Slot} / ${Price} / [Buy Now] [Add To Cart]`.

## 8. Were useful endpoints observed?
None beyond previous findings (Google reCAPTCHA, Pinterest link).

## 9. Suitability
- Source directory only: yes
- External cash comparison: **yes — best candidate so far**
- Offline parser from captured artifacts: **yes — rune name and price are extractable**
- Future approved collector: yes, if parser validates properly

## 10. Caveats
- Prices are per-unit asking prices, not completed sales.
- The page shows a limited set of runes (7 visible in capture).
- Need to verify the full rune list (all 33) by finding a dedicated runes page.
- Segment filters exist but it's unclear if they affect the displayed prices.
