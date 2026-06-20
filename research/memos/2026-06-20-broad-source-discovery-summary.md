# Broad Source Discovery Summary

Generated: 2026-06-20
Method: Camoufox browser smoke tests (4 sources, one page each, ~10s per source)

## Results

| Source | Rendered | Prices | Segments | Login? | Verdict |
|---|---|---|---|---|---|
| **IGGM** | ✅ | **$1.79–$8.99 (7 runes)** | PC/Xbox/Switch, Ladder/NL, SC/HC, ROTW | No | **Best candidate** — rune names + prices in rendered DOM |
| **Odealo** | ✅ | Per-item Base price (no $ prefix) | PC, Ladder/NL, SC/HC, ROTW | No | Promising — need rune-specific URL |
| **PlayerAuctions** | ✅ | Not on homepage | Ladder, Season | No | Need rune-specific URL |
| **YesGamers** | ✅ | Behind login | Ladder, NL, HC, Season, ROTW | **Yes** | Deferred — login wall |

## Top Sources for external_cash_prices v0

1. **IGGM** — rune prices directly visible ($1.79–$8.99). Segment filters for ladder, SC/HC, platform, ROTW. Clean DOM structure with rune name + slot + price.
2. **Odealo** — item prices visible in rendered DOM (Base price field). Need rune category page.
3. **items7** (static) — has $0.15–$2.85 prices but per-rune mapping not yet extractable.

## Sources Remaining browser_required (post-update)

- **g2g** — confirmed browser capture works. LoD/RoTW ambiguity unresolved. Offer pages crash.
- **playerauctions** — captured. Need rune-specific URL.
- **odealo** — captured. Need rune-specific URL.
- **iggm** — captured and most promising. Could move to offline_parse_candidate.
- **yesgamers** — login wall. Deferred.
- **ebay, eldorado, mmopixel, mulefactory, rpgstash** — not yet captured (all later priority).
- **chicksgold** — captured static, dynamic shell, low priority.

## Next 3 Captures

1. **IGGM dedicated runes page** — to get full 33-rune price list for parser prototype.
2. **Odealo runes marketplace** (`/games/diablo-2/marketplace/runes`) — to verify per-rune prices render.
3. **PlayerAuctions rune search** — filtered to show only rune listings.

## Sources Ready for Offline Parser

| Source | Status | Reason |
|---|---|---|
| **IGGM** | ✅ Now | 7 rune prices + names in rendered HTML. Clean DOM. |
| items7 | Partial | $0.15–$2.85 visible but per-rune mapping needed. |
| Odealo | Partial | Prices visible in rendered DOM but rune-specific page needed. |

## Site-Specific Blockers

| Site | Blocker |
|---|---|
| YesGamers | Login wall — cannot see prices or use segment filters without authentication. |
| G2G offer pages | Camoufox / Playwright JS error on offer-detail URLs — page-level bug. |
| PlayerAuctions homepage | Card selector finds navigation items, not rune listings. Need filtered URL. |
