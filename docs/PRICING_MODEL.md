# Pricing Model

## Principles

1. **Direct in-game completed trades are the source of truth for relative rune ratios.**
2. **External cash prices are not inputs to the in-game model.** They are comparison-only.
3. **Active listings are not completed trades.** Asking prices are not transaction prices.
4. **Segment separation is mandatory.** PC softcore ladder prices are not interchangeable with PC hardcore non-ladder.
5. **Missing segment metadata excludes or lowers confidence** for observations.

## Current Model

### Numeraire

Ist Rune = 1.0. Ist is used because:
- It is the most traded rune across all segments.
- It is a mid-tier rune — common enough for high volume, valuable enough that low-value items are not priced in fractions.
- The current pipeline selects all trades where one side is Ist.

_This remains model-versioned and testable._ Future versions may switch numeraires or use a basket of runes.

### Price Calculation

For each rune (excluding Ist) in each segment:

1. **Bid side:** Filter trades offering Ist for the target rune. Compute VWAP = sum(IstQty) / sum(RuneQty).
2. **Ask side:** Filter trades offering the target rune for Ist. Compute VWAP = sum(IstQty) / sum(RuneQty).
3. **Outlier filter:** Remove trades where IstsPerRune < 0.5 or > 50.0.
4. **Blended FMV:** (Bid_VWAP + Ask_VWAP) / 2 when both sides exist. Single side if only one exists.

### Output

Per-segment CSV with columns: Rune, Bid_Price, Bid_Count, Ask_Price, Ask_Count, Blended_FMV, Total_Trades.

### Known Gaps

- **AND trades** (multi-item requests) are extracted but not modeled. They represent ~10-20% of valid trades.
- **Non-Ist pairs** (e.g. Jah-for-Ber trades) are not used. Graph-based price inference from all rune pairs is future work.
- **No confidence score** is computed yet. Price stability, sample size, and spread are not surfaced.
- **No time-weighting.** All trades in the dataset are weighted equally regardless of age.
- **No multi-segment aggregation.** Each segment is priced independently.

## Future Model Improvements

| Improvement | Priority | Notes |
|---|---|---|
| Confidence score (spread + sample size) | High | Surface bid-ask spread, trade count, and recency |
| Time weighting | Medium | Weight recent trades higher |
| AND-trade modeling | Medium | Multi-item trades reveal additional price relationships |
| Graph-based pricing | Low | Use all rune pairs to infer prices via graph solving |
| Alternative numeraires | Low | Test Jah, Ber, or basket-based numeraire |
| Non-rune item pricing | Low | Harlequin Crest, Annihilus, Torch — requires roll/variant handling |

## External Cash-Price Comparison

Cash/RMT prices (PlayerAuctions, items7, etc.) are handled separately:

- **Stored separately** in `external_cash_prices.json`.
- **Never blended** into the in-game rune model.
- **Labelled clearly** on the website: "Cash listing price — may differ from in-game trade value."
- **Useful for:** Detecting divergence, understanding segment premium, identifying arbitrage.
- **Caveats:** Cash prices include transaction fees, minimum floors, and profit margins. Low-value items may have price floors that don't reflect in-game ratios.

## Source-Specific Notes

| Source | Class | Use in Model | Notes |
|---|---|---|---|
| Traderie API | completed_player_trades | Primary | Source of truth for relative rune ratios |
| PlayerAuctions | cash_market_listings | Comparison only | Structured `data-bind` format, segment-aware |
| items7 | cash_market_listings | Comparison only | Simple per-unit prices, no segment granularity |
| Odealo | cash_market_listings | Comparison only | React-dynamic, excellent segment UI |
| IGGM | cash_market_listings | Comparison only | Dynamic, good segment descriptions |
| d2jsp | forum_trade_posts | Reference only | FG-based economy, indirect conversion |
| diablo2.io | not yet evaluated | — | Future investigation target |
| Reddit | community_discussion | Qualitative only | Venue discovery, item candidates, sentiment |
