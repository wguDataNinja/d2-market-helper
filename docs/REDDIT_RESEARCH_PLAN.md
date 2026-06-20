# Reddit Research Plan

## Purpose

Reddit research is used to understand the current Diablo II: Resurrected economy, player language, trade venues, common price-check items, and whether the existing rune-pricing assumptions still hold.

This is not part of the production pricing pipeline. Reddit data is qualitative market research unless explicitly promoted into a modeled signal later.

## Target Subreddits

Initial:
- r/D2R_Marketplace
- r/Diablo_2_Resurrected
- r/diablo2

Optional later:
- r/Diablo

## Collection Strategy

Collection must be slow, staged, and human-gated.

The preferred workflow is:
1. Fetch recent posts only.
2. Browse posts manually.
3. Select high-signal posts.
4. Fetch comments only for selected posts.
5. Export selected research to markdown/jsonl.
6. Summarize findings for the roadmap and pricing model.

## Rate-Limit Posture

We prefer slow collection over ban risk.

Post fetching is relatively low risk:
- Up to 1,000 recent posts per subreddit.
- Use batches of approximately 100.
- Sleep between requests when supported.
- Save incrementally.

Comment fetching is higher risk:
- Fetch comments only after human selection.
- Avoid full comment-tree expansion by default.
- Sleep between selected posts.
- Save after each post.
- Keep runs resumable.
- Stop immediately on API errors, rate-limit warnings, or unusual failures.

Taking hours is acceptable. Avoid anything that looks like aggressive scraping.

## What To Look For

Classify posts/comments for:
- Frequently traded items.
- Common price-check items.
- Common currencies: Ist, Jah, Ber, forum gold, keys, perfect gems, USD references.
- Trade venues mentioned: Traderie, Diablo2.io, d2jsp, Discord, in-game lobbies.
- Economy complaints or changes.
- Ladder vs non-ladder differences.
- Hardcore vs softcore differences.
- New-player confusion.
- Scam/unfair-trade patterns.
- Current season or mod-driven demand changes.

## Search Terms

Useful terms:
- price check
- worth
- WTS
- WTB
- WTT
- trade
- Traderie
- d2jsp
- diablo2.io
- Jah
- Ber
- Ist
- Lo
- Ohm
- Sur
- rune value
- ladder economy
- non-ladder
- hardcore
- softcore

## Outputs

Store raw research under:
```text
research/reddit/raw/
```

Store selected post IDs under:
```text
research/reddit/selected/
```

Store exports under:
```text
research/reddit/exports/
```

Store summaries under:
```text
research/reddit/notes/
```

## Use In This Project

Reddit research should inform:
- Which items to track beyond runes.
- Whether Ist remains a useful numeraire.
- Which trade venues deserve source discovery.
- What users need from the website and browser tools.
- What warnings/disclaimers the product should show.

Reddit research should not directly set prices without a separate modeling decision.

## Item Profile Extraction

Reddit research should identify items that deserve first-class item profiles. When posts/comments repeatedly mention an item, create or update an item profile under `data/item_profiles/`.

Profiles should capture:
- gameplay role
- economic role
- common trade units
- segment sensitivity
- important rolls/variants
- common trade venues
- new-player confusion points
- scam or unfair-trade patterns
- whether the item can be modeled from structured trade data
- whether it should appear on the website, userscript, or research-only reports

Reddit should not directly determine prices. It should update item context, demand signals, source discovery, and modeling requirements.
