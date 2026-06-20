# Browser Capture Artifacts

Each directory under `captures/` represents one browser capture session.

## Layout

```
captures/{source_slug}_{YYYYMMDD_HHMM}/
├── page.html              # Rendered HTML after JS execution
├── screenshot.png         # Full-page screenshot
├── metadata.json          # Capture metadata (URL, filters, notes)
├── listing_samples.json   # Extracted listing/price samples
├── network_summary.json   # API endpoints observed in page source
└── source_review.md       # (optional) Review notes
```

## metadata.json

```json
{
  "source": "g2g",
  "captured_at": "2026-06-20T12:00:00Z",
  "target_url": "https://...",
  "final_url": "https://...",
  "capture_method": "camoufox (headless, sync_api)",
  "page_title": "Buy D2R Items...",
  "page_rendered": true,
  "login_required": false,
  "visible_listings_found": 20,
  "breadcrumb": [...],
  "selected_platform": "",
  "selected_ladder": "",
  "selected_hardcore": "",
  "selected_item": "",
  "price": "",
  "notes": [...]
}
```

## Rules

- One capture per directory. Do not add multiple captures to the same directory.
- Screenshots may be large (1-3 MB). They are not gitignored but should be kept.
- Never include credentials, cookies, or private data in metadata or network_summary.
- If a capture failed, include the error in `metadata.json` notes and keep the partial artifacts.
