# Odealo — Browser Smoke Review

## 1. Did the page render?
Yes. Title: "Buy D2R Items – Cheap & Secure | Odealo Marketplace". Breadcrumb: Home > D2R > Items. 17 listing cards found.

## 2. Were rune prices visible?
Not via `$` regex. However, listing samples show explicit per-item prices in a "Base price" field without `$` prefix: $20.00, $15.00, $1,000.00, $0.03. These are asking prices from individual sellers.

## 3. Were selected high-value item prices visible?
Yes — but only for items that happen to be on the first page. One listing mentions "Full Rejuvination Potion", another "Fire Warlock Complete build". No rune-specific listings visible on this page.

## 4. What segment filters exist?
Excellent: ladder, non-ladder, softcore, hardcore, rotw, pc detected in listing titles.

## 5. Are platform/ladder/hardcore/softcore/season visible?
Yes, embedded in listing titles: "1-PC Ladder", "7-PC Hardcore Ladder", "D2R Rotw Ladder Softcore".

## 6. Is the site static, JS-rendered, embedded JSON, API-driven, or unclear?
JS-rendered (React). Per-item prices are rendered in the DOM after hydration. JSON-LD AggregateOffer ($0.01-$999.99) was present in the static shell.

## 7. Could prices be parsed from rendered HTML?
Yes, if the right category page is used. The listing card structure is:
- Seller name
- Segment: "{quantity}-{platform} {mode}" (e.g. "1-PC Ladder", "7-PC Hardcore Ladder")
- Delivery time estimate
- Stock quantity
- Base price
- BUY NOW button

The runes category page (`/games/diablo-2/marketplace/runes`) would likely show per-rune prices.

## 8. Were useful endpoints observed?
None beyond previous findings (Google reCAPTCHA, static.odealo.com CDN).

## 9. Suitability
- Source directory only: yes
- External cash comparison: yes, with the runes category page
- Offline parser: yes, from browser-captured HTML on the right category page
- Future collector: maybe, after verifying rune page renders

## 10. Caveats
- The general "Items" page shows a mix of items. The rune-specific URL needs to be captured.
- Prices are per-unit "Base price" — not labeled as "$" in the DOM, just numeric.
- Segment info is embedded in listing titles (e.g. "1-PC Ladder"), not filter toggles.
