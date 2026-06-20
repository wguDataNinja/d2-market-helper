# Reddit Research Pass 1 — Learnings

Generated: 2026-06-20

## Scope

2,998 posts collected across three subreddits: r/D2R_Marketplace (1,000), r/Diablo_2_Resurrected (999), r/diablo2 (999).

Post metadata only. Comments were not fetched.

## Direct Market Signal

Only 8 of the 150 highest-comment posts contained direct market language (price check, worth, WTS, trade venue reference, currency discussion). The remaining 142 posts were general discussion, build help, show-off drops, memes, nostalgia, or lore.

The 8 candidates were:

- is this the best base for enigma? (Marketplace, 114c)
- this perfect Griffon's Eye just dropped. Taking offers! (Marketplace, 113c)
- What's a realistic ask for this? (Marketplace, 108c)
- Wondering how much will this go for (Marketplace, 76c)
- What is this worth? (Marketplace, 74c)
- the economy has changed so much even in d2r (diablo2, 66c)
- WTS: Rare Winged Harpoon (Marketplace, 64c)
- Why are Mosaic claws soooo expensive? (diablo2, 61c)

## Why Comment Fetch Was Deferred

The direct-market signal in the top-150 comment posts was thin. Only 8 posts warranted fetching, and several of those were low-comment Marketplace listings where the "discussion" is likely limited. The expected information yield from 150 comment-tree fetches was too low to justify the API cost and review time.

Future comment fetches should be hypothesis-targeted (e.g. "find posts discussing Ist/Jah/Ber ratios and fetch their comments") rather than broad "fetch everything with market keywords."

## What Reddit is Useful For

- **Venue discovery**: Traderie (45 mentions) and Discord (18 mentions, including Baal's Ledger bot) appeared as trade venue signals. d2jsp/FG appeared only 7 times, suggesting Reddit users primarily use Traderie or Discord for trading.
- **Player language**: "PGems" appeared 88+ times as a low-value pricing unit. "FG" and "d2jsp" appeared rarely but may dominate outside Reddit. "HR" (high rune) appeared as a generic category.
- **Item/profile candidates**: Enigma (86 mentions), Spirit (73), Grief (61) confirmed as top runewords. SoJ, Arachnid Mesh, Raven Frost, Dwarf Star, Maras identified as commonly traded uniques needing profiles.
- **New-player pain points**: Several posts expressed confusion about what items are worth, where to trade, and how to value items — confirming demand for a pricing tool.
- **Future targeted research**: Subreddit-specific searches (e.g. "price check Griffon's Eye" in D2R_Marketplace) would yield higher signal than broad top-150-by-comments.

## What Reddit is NOT Used For

- **Price calculation**: Reddit post metadata does not contain structured pricing data. Even comment prices would be anecdotal.
- **Market-share claims**: Reddit users are not representative of the full player or trader population.
- **Validating rune ratios**: Community sentiment on whether "Jah should be worth X Ist" is not a price signal.

## Cautious Findings

- **Traderie and Discord** appeared as relevant venue signals. Traderie is the dominant mentioned platform. Discord is secondary.
- **d2jsp/FG** appeared lightly in this Reddit sample (7 mentions across 2,998 posts) but may still dominate outside Reddit. Reddit may be a Traderie-leaning userbase.
- **PGems** appeared 88+ times as a pricing unit. This justifies future investigation into low-value currency modeling (sub-Ist pricing in PGems or other units).
- **Runewords** (Enigma, Spirit, Grief, Infinity, CTA) should be modeled primarily as demand drivers for their component runes, not as standalone priced items. The rune market is driven by runeword demand.
- **High-value uniques/charms** (Griffon's Eye, Annihilus, Hellfire Torch, Arachnid Mesh, SoJ) remain candidates for later site-based pricing if source data supports variant classification (rolls, sockets, ethereal status).

## Artifacts

| File | Purpose |
|---|---|
| `research/reddit/raw/` | 3 JSONL files (2,998 posts) |
| `research/reddit/selected/candidates_d2r_pass1.jsonl` | 742 high-signal candidates (broad) |
| `research/reddit/selected/comment_fetch_review_top150.jsonl` | Top 150 by comments (all subreddits) |
| `research/reddit/selected/comment_fetch_market_shortlist_pass1.jsonl` | 107 market-adjacent posts |
| `research/reddit/selected/comment_fetch_direct_market_pass1.jsonl` | 8 direct-market posts |
| `research/reddit/notes/2026-06-20-comment-fetch-review-top150.md` | Full review (150 posts) |
| `research/reddit/notes/2026-06-20-comment-fetch-market-shortlist-pass1.md` | Market shortlist (107 posts) |
| `research/reddit/notes/2026-06-20-comment-fetch-direct-market-pass1.md` | Direct-market shortlist (8 posts) |
| `research/item_candidates/unresolved_terms.jsonl` | 10 candidate items needing profiles |
| `scripts/reddit_extract_items.py` | Registry-based extraction tool |

## Decision: Move to Source/Site Discovery

The next research phase is inspecting downloaded pricing/trade sites to determine how rune prices and selected high-value item prices can be extracted or compared.
