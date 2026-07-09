# Traderie Userscript Readiness Boundary

**Date:** 2026-07-09
**Scope:** Workstream J — production-readiness boundary for the TraderieTools userscript.

---

## 1. Canonical version and source

| Attribute | Value |
|---|---|
| Repository | `github.com/wguDataNinja/TraderieTools` |
| Userscript file | `traderie-tools.user.js` |
| Version | `2026-06-26` (date-based, in `@version` metadata) |
| Branch | `main` |
| Current HEAD | `d2e8496` (1 commit ahead of `origin/main`) |

The userscript has no build step, no package manager, no CI, and no tests. It is installed directly via Tampermonkey or Greasymonkey from the `raw.githubusercontent.com` URL or (eventually) from GreasyFork.

There is no separate dev/production channel. The single `main` branch is the only version.

---

## 2. Build/release method

| Step | Method | Status |
|---|---|---|
| Develop | Edit `traderie-tools.user.js` directly | Current |
| Version | Update `@version` date in metadata | Manual — not automated |
| Package | No packaging needed (single-file script) | N/A |
| Release | Push to GitHub; users install from raw URL | Current |
| Publish | GreasyFork page | **BLOCKED** — GreasyFork URL contains placeholder `YOUR-SCRIPT-ID`; must be set up |
| CI | None | Would be useful but not required for a single-file userscript |

---

## 3. Compatibility assumptions with Traderie data/outputs

The userscript depends on:

| Data | Source | Compatibility risk |
|---|---|---|
| `rune_prices.json` | `raw.githubusercontent.com/wguDataNinja/TraderieTools/main/rune_prices.json` | The JSON file lives in the TraderieTools repo, not the `traderie` repo. VPS migration of the `traderie` repo does not affect this URL. No risk. |
| `traderie.com` DOM structure | Live website | The userscript parses the traderie.com DOM. If the website changes its HTML structure, the userscript may break. This is a normal maintenance risk, not a VPS migration concern. |

The userscript does NOT consume:
- Any Traderie PostgreSQL data
- Any `traderie` repo product files (`data/products/*.json`)
- Any health output
- Any backup or archive artifacts

Therefore, VPS migration of the main `traderie` repo has **zero impact** on the userscript.

---

## 4. Required browser/manual checks

Before a userscript release:

1. Navigate to a Traderie listing page (e.g., `traderie.com/d2r/playstation/softcore/...`).
2. Verify the UI panel loads (draggable, resizable).
3. Verify the ad blocker toggle works.
4. Verify rune pricing badges appear on D2R listings.
5. Verify bookmark save/load works across page navigation (SPA hook).
6. Verify rune prices load from GitHub (check `localStorage` for cache timestamp).
7. Verify no console errors.

No automated test suite exists for these checks. They remain manual.

---

## 5. Safe rollback method

```javascript
// In Tampermonkey dashboard:
// 1. Disable the script by toggling the switch
// 2. Or install an older version from GreasyFork / GitHub releases
```

Git rollback: `git checkout <previous-SHA>` on the TraderieTools repo, then point users to the old raw URL.

No database rollback needed — the userscript stores only `localStorage` data (bookmarks, toggles, panel state, price cache). Clearing `localStorage` returns the script to clean state.

---

## 6. VPS migration impact

The userscript depends on one URL: `raw.githubusercontent.com/wguDataNinja/TraderieTools/main/rune_prices.json`.

This URL is independent of the VPS, the `traderie` repo deployment, and all PostgreSQL infrastructure. The VPS migration of the main `traderie` repo does not change this URL.

**No userscript changes are needed for VPS migration.**

---

## 7. AND-trade handling

AND-trades (listings where the seller wants multiple rune types) are recognized by the `has_and_prices` flag. The userscript computes a combined Ist value for both sides of the trade. The fairness evaluation sets `value_ist_sum` from individual rune values. AND-trade detection depends on DOM parsing of the listing page.

This behavior is manual-review-only: the userscript surfaces fairness information but does not auto-trade or auto-accept. The user must review the computed values and decide manually.

---

## 8. Summary

| Concern | Assessment |
|---|---|
| VPS migration impact | None |
| Dependency on Traderie repo | None (separate repo) |
| Dependency on Traderie data files | Only `rune_prices.json` in its own repo |
| Dependency on Traderie API | None |
| Dependency on VPS infrastructure | None |
| Build/CI required | No (single-file script) |
| GreasyFork publishing | Not yet set up (placeholder URL) |
| Tests | None |
| Rollback method | Disable in Tampermonkey or install older version |
| Versioning | Manual date-based `@version` |
