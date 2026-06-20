# Source Discovery Workflow

## Overview

Source discovery is the process of finding, capturing, evaluating, and optionally integrating pricing/trade sources into the D2R Market Helper project.

## Workflow Stages

### 1. Discovery

- Search for D2R trade/pricing sites via Google, forum mentions, Reddit, existing directories.
- Add the source to `data/source_manifest.json` with status `discovered`.
- Note the URL and any known segment/price information.
- Create `research/sources/{source_slug}.md` with initial notes.

### 2. Static Capture (if applicable)

- Download the page HTML: `curl -o research/sources/downloads/{source_slug}.html {url}`
- Save to `research/sources/downloads/rune_sources_YYYY-MM-DD/` organized by batch date.
- If prices are visible in static HTML, extract samples and update the source notes.

### 3. Browser Capture (if JS-rendered)

- Use Camoufox from `playwright_workbench/.venv` for JS-heavy sites.
- Run `scripts/capture_g2g_page.py` (or a source-specific script) for one page at a time.
- Save artifacts to `research/sources/captures/{source_slug}_{YYYYMMDD_HHMM}/`.
- Required artifacts: `page.html`, `screenshot.png`, `metadata.json`, `listing_samples.json`.
- Optional: `network_summary.json` if HAR or endpoint patterns are captured.

### 4. Offline Artifact Inspection

- Review saved HTML for price structure, segment filters, embedded JSON, API endpoints.
- Extract sample prices where visible.
- Update `research/sources/{source_slug}.md` with findings.
- Update `data/source_manifest.json` status to `captured_static` or `captured_browser`.

### 5. Parser Prototype (if evidence supports it)

- Write a small parser script at `scripts/parse_{source_slug}.py`.
- Parser must work from saved artifacts only — no live network fetches.
- Output: extract prices in a structured format matching the `external_cash_prices.json` schema.
- Update manifest status to `parser_prototype_ready`.

### 6. Integration

- After schema and segment validation, the source can be integrated into the website data model.
- Integration means the source appears in `source_directory.json` and its prices appear on the website.
- Update manifest status to `integrated`.

## Principles

| Principle | Rule |
|---|---|
| **No live scraping** | All extraction is from saved artifacts. No live crawlers. |
| **One page at a time** | No pagination loops, no bulk captures, no scheduled collection. |
| **No login bypass** | Do not use stored credentials, login profiles, or bypass auth. |
| **Evidence before parser** | Do not write parsers for sources without captured artifact evidence. |
| **Segment-aware** | Document which segment filters each source supports before any integration. |
| **Cash is separate** | Cash-market sources are comparison-only. Never blend into in-game rune values. |
| **Defer when stuck** | If a source causes browser errors, anti-bot challenges, or requires login, defer it. |

## When to Stop

Stop investigating a source if:

- It requires login or paid access to see prices.
- It has no segment filter capability (ladder, SC/HC, platform).
- The page triggers anti-bot challenges that Camoufox cannot bypass.
- The data quality is worse than existing sources (e.g., fewer items, less frequent updates, no segment metadata).
- The source is a general marketplace with minimal D2R-specific content.

## Artifact Lifecycle

- Downloaded HTML: kept in `research/sources/downloads/` — not gitignored, but large files may be excluded.
- Browser captures: kept in `research/sources/captures/` — screenshots and HTML may be large.
- Source notes: kept in `research/sources/{slug}.md` — always committed.
- Manifest: kept in `data/source_manifest.json` — always committed.
- Validation: run `python scripts/validate_source_manifest.py` after every manifest change.
