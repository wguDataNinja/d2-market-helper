# Diablo2.io Sold-Search Fixture

Date: 2026-06-20

## Fixture Location

```
research/sources/captures/diablo2io/2026-06-20_jah_sold_search/rendered.html
```

## Source URL

```
https://diablo2.io/search.php?keywords=Jah&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=43
```

## Parser

```
scripts/parse_diablo2io_sold_search_offline.py
```

## Output

```
data/research/diablo2io_sold_jah_trades.sample.json
```

## Parser Rules

- Fixture-only. No network.
- Extract SOLD trade rows from rendered HTML.
- Preserve raw row text.
- Parse: WTS/WTB, target quantity, target item, sold time, seller, buyer, consideration.
- Every row gets `use_in_model: false`.
- Output is research-only.

## HTML Structure

Each trade row is inside a `<div class="zf-container zf-container-trade">` container.

Key selectors:
- `z-trusty-wtbs` — WTS/WTB badge (title attribute)
- `z-trusty-sold` — SOLD badge
- `z-trade-mini-icon` — item icon (e.g., `runeJo_sicon.png` for Jah)
- `z-inline-trade-desc` — description body (`<t>` tag)
- `zf-topic-deets` — sale line: "Sold <time> by <seller> to <buyer> for <items>"
- Segment icons: `zi-nonladder`, `zi-pc`, `zi-softcore`, `zi-americas`, `zi-tinylogrotw`

## Limitations

- Parser does not validate that rows represent actual completed trades — it trusts the SOLD badge.
- Some rows lack buyer or accepted consideration.
- Segment filters parsed from visible HTML icon classes — not from filter controls.
- Pagination not yet analyzed — this is a single-page fixture.
- Description text may conflict with structured sale line.
