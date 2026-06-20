# Diablo2.io Ber Sold-Search Fixture

## Capture Instructions

1. Open in a regular browser (Chrome/Firefox):
   https://diablo2.io/search.php?keywords=Ber&terms=all&author=&fid%5B%5D=16&sc=0&sf=titleonly&sr=topics&sk=t&sd=d&st=0&ch=300&t=0&submit=Search&activesold=1&uitemid=45

2. Wait for the page to fully load (including "Loading trades..." spinner).

3. Right-click → Save As → "Web Page, HTML Only".

4. Save to: research/sources/captures/diablo2io/2026-06-20_ber_sold_search/rendered.html

## After Capture

Run the parser:
python3 scripts/parse_diablo2io_sold_search_offline.py --item ber

Expected output: data/research/diablo2io_sold_ber_trades.sample.json

All rows will have use_in_model=false.
