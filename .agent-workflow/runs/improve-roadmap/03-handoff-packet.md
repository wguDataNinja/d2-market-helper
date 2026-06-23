# Handoff Packet — Codex: Rewrite ROADMAP.md for Zero-Question Execution

## Recipient Mode

**Capability:** `repo_aware` (Codex CLI can read files and run commands in the repo)
**Execution:** `output: file_overwrite` (you will overwrite `ROADMAP.md` only)
**Constraints Checked Before Accepting:** available disk space, repo is on a writable branch, target file exists

---

## 1. Task Goal

Rewrite `ROADMAP.md` (`/Users/buddy/projects/traderie/ROADMAP.md`) so that a **weak coding agent** can execute every work session without:
- Asking the user a question
- Exploring the repo to discover file paths, schemas, or CLI flags
- Making any judgment call about what to do next
- Deciding between alternative approaches

**Definition of "weak agent":**
- Can run shell commands you give it, check exit codes, read files at exact paths, and parse structured output
- **Cannot** explore the repo, infer intent from vague descriptions, or make trade-off decisions
- **Cannot** decide whether a step is "optional," "conditional," or "nice to have"
- **Cannot** look up CLI flags by running `--help` — every command in the roadmap must be fully specified

The rewritten `ROADMAP.md` must be so precise that a human could hand it to a junior intern with no knowledge of the project, and that intern could execute all 4 sessions by copying-and-pasting each command in order.

---

## 2. Current State (Point A)

The current `ROADMAP.md` (read it at step 1 below) has 6 work sessions with vague, ambiguous steps:

| Session | Example of Vagueness | Why It Fails for a Weak Agent |
|---------|----------------------|-------------------------------|
| 1 | "Compare observation counts vs last generation" | No baseline specified, no comparison tool, no pass/fail criteria |
| 1 | `build_traderie_dataset_from_history.py --write-research` | No explanation of what this outputs or where — agent can't validate success |
| 2 | "Monitor 2-3 launchd cycles" | No concrete monitoring command, no definition of a "cycle," no decision tree for pass/fail |
| 2 | "If still failing: add skip list" | Ambiguous condition — what constitutes "still failing"? No count threshold specified |
| 2 | "Consider reducing hardcore timeout" | "Consider" is a judgment call; weak agent cannot decide |
| 3 | "Add `snapshot_io` calls to `parse_d2stock_rss.py`" | No mention of the existing parser structure, where exactly to insert calls, or what data to pass |
| 3 | "Update `collection_status.py` to detect new cash source snapshots" | Ambiguous — is a code change needed, or does auto-detection already work? |
| 4 | "Responsive layout fixes (test at mobile widths)" | No breakpoint specified, no testing tool, no acceptance criteria |
| 4 | "Cash price comparison panel (read-only, labeled)" | No spec, no component structure, no data model reference |
| 5-6 | Labeled "Optional" with "If needed" / "If viable" guards | Weak agent cannot determine optionality; these sessions create ambiguity even if skipped |

The current roadmap also includes:
- A **Progress Summary** table (irrelevant to execution — remove)
- A **Product Vision + Core Rules** section (preserve — defines project identity)
- An **Invariants** section (preserve **byte-identical** — non-negotiable policy)
- **Sessions 5-6** that are optional (move to backlog, do not include in the rewrite)

---

## 3. Desired State (Point B)

A `ROADMAP.md` where any single session can be handed to a naive agent with a single "run Session N" instruction. Every checkbox item in every session must include:

| Component | Requirement | Example |
|-----------|-------------|---------|
| **Exact command** | Full `python3 scripts/foo.py --flag value` from repo root | `python3 scripts/build_traderie_dataset_from_history.py --write-research` |
| **Relative path to script** | Always specify exact relative path | `scripts/build_traderie_dataset_from_history.py` (not `build_dataset.py`) |
| **Input paths (with expectations)** | State what files/dirs must pre-exist | "Requires `data/history/traderie/*/*.jsonl` from accumulated snapshots" |
| **Output paths** | State exact file(s) produced | "Writes `data/research/extracted_trades_{segment}.csv` (1 per segment, 4 files total)" |
| **Success signal** | Concrete observable to check after running | "Exit code 0. Check: `wc -l data/research/extracted_trades_pc_sc_l.csv` shows > 1000 lines" |
| **Validation command** | A one-liner to confirm the step worked | `python3 scripts/validate_in_game_rune_values.py && echo "PASS"` |
| **Rollback / failure handling** | What to do if the step fails | "If exit code != 0, run `python3 scripts/collection_status.py` and report the output" |

**Structural requirements:**
- Keep the **Product Vision + Core Rules** block as-is (it's identity, not execution)
- Remove the **Progress Summary** table entirely
- Keep exactly **4 sessions** (drop Sessions 5-6)
- Keep the **Invariants** section **byte-identical** to the current version
- Do not add any new top-level sections
- Remove the `#driver:` annotations (they refer to agent routing, not execution steps)

**Format requirements:**
- Each session is a level-2 heading (`## Session N — Title`)
- Each step is a markdown checkbox (`- [ ]`) followed by a **bold command** or **bold action description**, then a plain-text explanation of what the command does, what it produces, and how to validate it
- Every command is a single-line string starting with `python3 scripts/` or `npm run` (from repo root)
- No ambiguous language: no "consider," "evaluate," "if needed," "optionally," "maybe," "monitor"
- Full paths always relative to repo root (no `~`, no `/Users/buddy/...`)

---

## 4. Key Constraints (Your Binding Rules)

### What you (Codex) may do:
- Read files listed in Section 6 (and ONLY those files)
- Overwrite `ROADMAP.md` with the rewritten content
- Print your analysis to stdout (not into the file)

### What you (Codex) may NOT do:
- **Do NOT execute any scripts.** This is a plan-only task. No `python3`, `npm`, `launchctl`, or any other command execution.
- **Do NOT edit any file other than `ROADMAP.md`.**
- **Do NOT create new files** (backups, drafts, or otherwise).
- **Do NOT make network requests.**
- **Do NOT install packages or modify dependencies.**
- **Do NOT run `git` commands.**
- **Do NOT change the Invariants section.** It must be **byte-identical** to the original after the rewrite.

### What the roadmap must enforce:
- **Every command must explicitly include all flags.** A weak agent must never need to look up `--help`.
- **Every step that produces output must say what to check.** "Check that X file exists with Y properties" is the minimum.
- **Every step that could fail must include an explicit "if this fails" instruction.** Not "if needed" — a concrete alternative path.
- **All file paths must be relative to the repo root.** The repo root is the working directory for all commands.
- **Sessions 5-6 must not appear anywhere in the file.** They move to a separate backlog.
- **The Product Vision, Core Rules, and Invariants sections must be preserved.** Only the Progress Summary table and Session 5-6 are removed.
- **No conditional/optional language.** Every session must be definite — you can always run it and get a pass/fail result.
- **Failure handling must be concrete.** Instead of "if this fails, investigate," write "if exit code != 0, run `python3 scripts/collection_status.py` and send its output as a bug report."

---

## 5. Non-Goals

These are explicitly **not** part of your task. If you feel tempted to do any of these, stop and refocus on the 4-session rewrite:

- **Do not design new pipeline stages, data products, or architecture.** The pipeline is established; the roadmap schedules execution of existing work.
- **Do not modify, suggest modifications to, or add code snippets for any source file.** The roadmap may reference files that future agents will modify, but you must not include code diffs — only commands to run and files to edit.
- **Do not add a build system, task runner, Makefile, or shell script.**
- **Do not add scheduling/deployment instructions** (cron, launchd, CI) beyond what's already in the roadmap.
- **Do not add new sessions.** Exactly 4 sessions. No more.
- **Do not reorganize the repo** or suggest directory structure changes.
- **Do not add a "Prerequisites" section or setup steps.** Sessions assume the repo is already configured.
- **Do not add the Progress Summary table back.**
- **Do not add `#driver:` annotations or any other agent-routing metadata.**
- **Do not blend Sessions 1-4 with optional follow-ups.** Each session is standalone and complete.

---

## 6. Relevant Context

### 6.1 Files You Must Read (in this order, before writing)

Read ALL of these. Your analysis depends on understanding every CLI interface, data path, and component structure.

**Pipeline scripts (Session 1):**

| Order | File | What to Extract |
|-------|------|-----------------|
| 1 | `ROADMAP.md` | The current roadmap (to rewrite). UNDERSTAND what Sessions 1-4 are trying to accomplish. |
| 2 | `scripts/build_traderie_dataset_from_history.py` (lines 1-30, 180-230, 250-300) | CLI flags (`--write-research`, `--compare`, `--segment`), input paths (`data/history/traderie/{seg}/completed_trades_{seg}.jsonl`), output paths (`data/research/extracted_trades_{seg}.csv`, `data/research/traderie_history_dataset_{seg}.json`), what the `--write-research` flag controls |
| 3 | `scripts/calculate_rune_prices.py` (full file, 112 lines) | `--input-dir` flag (default `data/extracted/`, but Session 1 uses `data/research/`), input format (`extracted_trades_{seg}.csv`), output path (`data/prices/rune_prices_{seg}.csv`) |
| 4 | `scripts/generate_prices_json.py` (lines 1-70, 140-end) | Inputs from `data/prices/rune_prices_{seg}.csv`, outputs to `data/products/in_game_rune_values.json` and `data/products/traderie_tools_prices.json` |
| 5 | `scripts/validate_in_game_rune_values.py` (lines 1-50) | What it checks (schema version, segment presence, required fields), exit code behavior |
| 6 | `scripts/validate_external_cash_prices.py` (lines 1-50) | What it checks (schema version, observation fields, `use_in_model=false`, source manifest linkage), exit code behavior |

**Hardcore monitoring scripts (Session 2):**

| Order | File | What to Extract |
|-------|------|-----------------|
| 7 | `scripts/snapshot_traderie.py` (lines 1-40, 300-366) | Timeout constants (10s softcore, 30s hardcore, 2-3 attempts, 5s/15s backoff), segment detection (`HARDCORE_SEGMENTS = {"pc_hc_l", "pc_hc_nl"}`), the `--segment` and `--item` flags, output paths |
| 8 | `scripts/collection_status.py` (lines 1-30, 188-213, 216-260) | The `collect_logs()` function that counts ReadTimeouts from `logs/launchd/snapshot-traderie.err.log`, the text report format, exit code behavior |
| 9 | `docs/COLLECTION_RUNBOOK.md` (lines 43-72) | The Traderie section showing the snapshot collector command, timeout/retry rationale, and output path conventions |

**Snapshot integration scripts (Session 3):**

| Order | File | What to Extract |
|-------|------|-----------------|
| 10 | `scripts/lib/snapshot_io.py` (full file, 114 lines) | The full API: `write_raw_snapshot(data, source)`, `write_normalized_snapshot(observations, source)`, `append_history(source, dataset, observations)`, `observation_key(obs)`, `content_hash(obs)`, all output path patterns |
| 11 | `scripts/parse_d2stock_rss.py` (lines 1-60, 200-291) | Current output path (`data/external/d2stock_cash_prices.json`), the `--offline` flag, the observation structure (especially `source_slug`, `item_name`, `price_usd`, `captured_at`), where observations are assembled |
| 12 | `scripts/parse_iggm_offline.py` (lines 1-60, 150-189) | Current output path (`data/external/iggm_cash_prices.json`), the `--input-dir` flag, the observation structure |
| 13 | `docs/COLLECTION_RUNBOOK.md` (lines 117-180) | The D2Stock and IGGM sections showing the "Needed: Add snapshot_io calls" notes, output paths (current and planned) |
| 14 | `scripts/collection_status.py` (lines 164-185) | The `collect_cash_snapshots()` function — currently iterates `data/snapshots/normalized/` and auto-detects any non-traderie source directory. **This means no code change is needed for auto-detection once parsers write snapshots.** The roadmap step should be: "Verify collection_status.py shows the new snapshots" not "Update collection_status.py". |

**UI work scripts (Session 4):**

| Order | File | What to Extract |
|-------|------|-----------------|
| 15 | `web/src/` (directory listing — list, do not read every file) | Component hierarchy: `pages/` (Home, Runes, Sources, Methodology) and `components/` (CashDisclaimer, ConfidenceBadge, Layout, SegmentSelector, StatusBadge) |
| 16 | `web/src/pages/Runes.tsx` (first 20 lines for imports/structure) | The main dashboard page structure — where rune prices, confidence, and segments are rendered |
| 17 | `web/src/components/SegmentSelector.tsx` (first 20 lines) | How segment selection works (URL query param `?segment=`) |
| 18 | `web/src/components/ConfidenceBadge.tsx` (first 20 lines) | Current confidence display — understand what exists to extend |
| 19 | `web/src/data/` (directory listing) | What data files the web app imports at build time |

**Data files:**

| Order | File | What to Extract |
|-------|------|-----------------|
| 20 | `data/products/in_game_rune_values.json` (lines 1-50) | Schema structure: `segments.{pc_sc_l,pc_sc_nl,pc_hc_l,pc_hc_nl}.runes.{rune}.{value_ist,confidence,bid_price,...}` |
| 21 | `data/products/external_cash_prices.sample.json` (lines 1-50) | Schema structure: `sources[]` with `observation_count`, `observations[]` with `source_slug, item_name, price_usd, segment_confidence` |

### 6.2 Pipeline Data Flow (for Session 1 precision)

The current ROADMAP.md Session 1 uses the **history-based pipeline** (not the legacy `fetch_completed_trades.py` → `extract_rune_trades.py` pipeline documented in COLLECTION_RUNBOOK.md's "Full Pipeline Command Sequence"). The history-based pipeline is the correct one for regeneration:

```
step 1: build_traderie_dataset_from_history.py --write-research
  INPUT:  data/history/traderie/{seg}/completed_trades_{seg}.jsonl   (4 files)
  OUTPUT: data/research/extracted_trades_{seg}.csv                   (4 files)
          data/research/traderie_history_dataset_{seg}.json          (4 files, research metadata)

step 2: calculate_rune_prices.py --input-dir data/research
  INPUT:  data/research/extracted_trades_{seg}.csv                   (4 files)
  OUTPUT: data/prices/rune_prices_{seg}.csv                          (4 files)

step 3: generate_prices_json.py
  INPUT:  data/prices/rune_prices_{seg}.csv                          (4 files)
  OUTPUT: data/products/in_game_rune_values.json
          data/products/traderie_tools_prices.json

step 4: validate_in_game_rune_values.py
  INPUT:  data/products/in_game_rune_values.json
          data/products/traderie_tools_prices.json
  OUTPUT: exit code 0 = PASS, exit code 1 = FAIL (prints errors to stdout)

step 5: validate_external_cash_prices.py
  INPUT:  data/products/external_cash_prices.sample.json
  OUTPUT: exit code 0 = PASS, exit code 1 = FAIL (prints errors to stdout)
```

### 6.3 Current Product State (as of 2026-06-22)

**`data/products/in_game_rune_values.json`:**
- Schema: v0.1
- 4 segments: pc_sc_l, pc_sc_nl, pc_hc_l, pc_hc_nl
- 92 rune observations total (~23 per segment)
- 2,570 modeled trades across all segments
- `source_window_label`: "rolling_recent_trades_50_cap"
- Confidence levels: high (50+ trades), medium (15-49), low (1-14), unavailable (0)

**`data/products/external_cash_prices.sample.json`:**
- Schema: v0.2
- 271 observations across 4 sources (IGGM: 30, ItemNow: 42, D2Stock: 199, items7: 0)
- All observations set `use_in_model=false`
- `source_window_label`: "current_snapshot"

### 6.4 History File Sizes (as of 2026-06-22)

```
data/history/traderie/pc_sc_l/completed_trades_pc_sc_l.jsonl   — 17,600 rows
data/history/traderie/pc_sc_nl/completed_trades_pc_sc_nl.jsonl — 17,700 rows
data/history/traderie/pc_hc_l/completed_trades_pc_hc_l.jsonl   — 16,342 rows
data/history/traderie/pc_hc_nl/completed_trades_pc_hc_nl.jsonl —  6,906 rows
```

These are approximately **10× larger** than the ~1,700 rows per segment that existed when products were last generated (2026-06-20). The regeneration should produce significantly higher observation counts.

### 6.5 Snapshot Collector Parameters (for Session 2 precision)

From `scripts/snapshot_traderie.py` (lines 28-42):

| Parameter | Softcore | Hardcore |
|-----------|----------|----------|
| Timeout | 10s | 30s |
| Max attempts | 3 | 2 |
| Backoff | 5s, 15s | 5s, 15s |
| Items × segments | 32 × 4 = 128 total requests per run |

Hardcore segment slugs: `pc_hc_l`, `pc_hc_nl`
Items list: `data/item_ids.json` (~70 items across Runes, Keys, selected uniques)

**Current failure rate:** 16 ReadTimeouts on recent runs (all hardcore). Exit code 1.

The roadmap Session 2 should specify concrete monitoring steps:
- Run `python3 scripts/collection_status.py` before and after
- Check `logs/launchd/snapshot-traderie.err.log` for ReadTimeout count
- Run a single hardcore segment manually: `python3 scripts/snapshot_traderie.py --segment pc_hc_l`
- The jitter fix (5-7s random delay instead of fixed 5s) and reduced hardcore attempts (3→2) were already deployed

### 6.6 Current Parser Structures (for Session 3 precision)

**`scripts/parse_d2stock_rss.py`:**
- Currently outputs to `data/external/d2stock_cash_prices.json`
- Has an `--offline` flag for fixture-based testing
- Observations are assembled in a list of dicts with keys: `source_slug` (hardcoded `"d2stock"`), `item_name`, `price_usd`, `currency`, `captured_at`, `segment_confidence`, etc.
- After adding `snapshot_io` calls, the parser should also output to:
  - `data/snapshots/raw/d2stock/{ts}/response.json`
  - `data/snapshots/normalized/d2stock/{ts}.json`
  - `data/history/d2stock/cash_prices.jsonl`

**`scripts/parse_iggm_offline.py`:**
- Currently outputs to `data/external/iggm_cash_prices.json`
- Has `--input-dir` for fixture directory
- Observations assembled similarly with `source_slug` hardcoded `"iggm"`
- Planned output paths (same pattern as d2stock, but `iggm` instead of `d2stock`)

**Important for Session 3:** `collection_status.py`'s `collect_cash_snapshots()` function (line 164-185) iterates `data/snapshots/normalized/` and **auto-discovers** any non-traderie source directory. Once parsers write snapshots via `snapshot_io`, the status script will automatically report them. **No code change is needed** in `collection_status.py` — the step should be "Verify collection_status.py shows the new snapshots" rather than "Update collection_status.py to detect new cash source snapshots."

### 6.7 Web Component Tree (for Session 4 precision)

```
web/src/
├── pages/
│   ├── Home.tsx          — Market overview landing page
│   ├── Runes.tsx         — Full rune dashboard (main price display)
│   ├── Sources.tsx       — Source directory / transparency ledger
│   └── Methodology.tsx   — About / methodology page
├── components/
│   ├── CashDisclaimer.tsx    — "Cash prices are comparison-only" banner
│   ├── ConfidenceBadge.tsx   — high/medium/low/unavailable badge
│   ├── Layout.tsx            — Shared layout shell
│   ├── SegmentSelector.tsx   — Dropdown/buttons, uses `?segment=` URL param
│   └── StatusBadge.tsx       — Source status indicator
├── data/                    — Build-time data imports (product JSONs)
├── App.tsx                  — Router + top-level layout
├── App.css                  — Global styles
├── styles/                  — Additional stylesheets
└── main.tsx                 — Entry point
```

For Session 4 (UI polish), the roadmap must reference these exact components when describing what to modify. Example: "Edit `web/src/components/ConfidenceBadge.tsx` to add a tooltip showing the `total_trades` count" instead of "Add confidence tooltips."

---

## 7. Decision Points (Resolve These in Your Analysis)

These are judgment calls you must make and explain in your stdout analysis (not in ROADMAP.md). Each requires a clear statement of what you decided and why.

### 7.1 Session 1 — What validation criteria for "observation counts grew"?

The current roadmap says "Compare observation counts vs last generation." The last generation (2026-06-20) had:
- pc_sc_l: 1,344 trades
- pc_sc_nl: 172 trades
- pc_hc_l: 117 trades
- pc_hc_nl: 48 trades

The history files now have 6,900-17,600 rows per segment.

**Decision needed:** What is the minimum expected observation count per segment after regeneration? Define a concrete threshold (e.g., "pc_sc_l ≥ 3,000 trades" or "all segments ≥ 5× previous count").

### 7.2 Session 2 — What is the pass/fail threshold for "hardcore reliability improved"?

**Decision needed:** After monitoring N launchd cycles (specify N), what ReadTimeout count constitutes failure? Example: "If ReadTimeout count in the last 24h (from `logs/launchd/snapshot-traderie.err.log`) is ≤ 5, the fix helped. If > 5, proceed to troubleshooting steps."

### 7.3 Session 2 — What are the exact troubleshooting steps after detecting failure?

The current roadmap says "add skip list for items that consistently time out on hardcore" and "collect timeout stats per item."

**Decision needed:** Convert these into concrete commands:
- What command collects per-item timeout stats? (Could be `grep` on error logs, or a small inline script.)
- What is the format of the skip list? (A set literal in `snapshot_traderie.py` or a JSON file?)
- What is the concrete timeout-reduction command? (Edit the constant `HARDCORE_REQUEST_TIMEOUT_SECONDS` from 30 to 20.)

### 7.4 Session 3 — Is `collection_status.py` auto-detection sufficient, or is a code change needed?

**Decision needed:** After adding `snapshot_io` calls to both parsers and running them, verify that `python3 scripts/collection_status.py` shows the new sources in the "Cash Source Snapshots" section. If yes, the step is "Run collection_status.py and confirm it shows d2stock and iggm snapshots." If no (because `collect_cash_snapshots()` has a specific filter you discover), the step must include editing `collection_status.py`.

### 7.5 Session 3 — The `generate_external_cash_prices.py` re-run

After parsers are updated, the external cash product needs regeneration. The command is `python3 scripts/generate_external_cash_prices.py` (reads from `data/external/*.json`, writes to `data/products/external_cash_prices.sample.json`).

**Decision needed:** Should this be an explicit step in Session 3, or is it implied by the existing pipeline? Make it explicit.

### 7.6 Session 4 — Specific acceptance criteria for each UI change

**Decision needed:** For each UI checkbox, define exact acceptance criteria:
- "Source freshness indicators": What data field drives this? (e.g., `generated_at` from product JSON — check it exists and is recent)
- "Confidence tooltips": Which component to modify? What tooltip library or DOM approach? (e.g., add `title` attribute to existing `ConfidenceBadge`)
- "Segment selector persistence": What mechanism? (URL `?segment=` already exists — verify it persists on navigation)
- "Responsive layout": What breakpoints? (e.g., test at 375px, 768px, 1024px using browser dev tools)
- "Cash price comparison panel": What data source? What component layout? (read from `external_cash_prices.sample.json`, place on Runes page alongside in-game values)

---

## 8. Validation Expectations

After you write `ROADMAP.md`, verify each of these conditions. If any fail, fix before finishing.

### Structural checks (do these by reading the file):

- [ ] **No Sessions 5 or 6.** Grep for `Session 5` and `Session 6` — must not match.
- [ ] **No `#driver:` annotations.** Grep for `#driver` — must not match.
- [ ] **No Progress Summary table.** Grep for `| Area | Status |` — must not match.
- [ ] **No "optional," "consider," "if needed," "evaluate," "maybe," "monitor"** in session steps. Grep for these words in the session sections — must not match (exclude the Invariants section).
- [ ] **Invariants section is byte-identical** to the original. Run `diff <(sed -n '/^## Invariants/,$ p' ROADMAP.md) <(echo '<original invariants>')` or manually verify each bullet matches exactly.
- [ ] **Product Vision + Core Rules** section is preserved (not deleted, not reworded).
- [ ] **Exactly 4 sessions** (headings `## Session 1` through `## Session 4`). No `## Session 0` or `## Session 5`.

### Content checks (do these by reading the file):

- [ ] **Every checkbox contains an exact command** (starting with `python3 scripts/`, `npm run`, or similar).
- [ ] **Every command explicitly states ALL flags.** No hidden defaults.
- [ ] **Every step that produces output says what file(s) to expect** and how to verify them.
- [ ] **Every validation step has a concrete success signal** ("exit code 0", "file exists with >N lines", "specific string in output").
- [ ] **Every step that could fail has explicit failure handling** ("if exit code != 0, run X and report Y").
- [ ] **All file paths are relative to repo root.** No absolute paths like `/Users/buddy/...`, no `~` shortcuts.
- [ ] **No `#driver: worker` / orchestrator routing metadata.**

### Edge cases:

- [ ] **If you reference scripts that produce multiple output files**, each output path is listed.
- [ ] **If you reference a script that has both online and offline modes** (`--offline`), the roadmap specifies which mode to use and when.
- [ ] **If a step depends on a fixture file existing** (IGGM parser), the roadmap says exactly where to place the fixture before running.

---

## 9. Output Format

### What goes to stdout (your analysis):

1. A brief analysis section (5-10 sentences) identifying the key ambiguities in the current `ROADMAP.md` and how your rewrite resolves them.
2. Your answers to each Decision Point in Section 7 (what you decided and why).

Do NOT put this analysis into `ROADMAP.md`.

### What goes into `ROADMAP.md`:

Only the rewritten markdown content. No preamble, no postscript, no commentary.

The file structure must be:

```markdown
# D2R Market Helper — Project Roadmap

## Product Vision

[verbatim from current file — Core Rules included]

---

## Proposed Work Sessions

### Session 1 — [Title]
- [ ] **`python3 scripts/...`** — explanation. Output: path. Validate: command.
- [ ] ...

### Session 2 — [Title]
- [ ] ...

### Session 3 — [Title]
- [ ] ...

### Session 4 — [Title]
- [ ] ...

---

## Invariants

[byte-identical from current file]
```

---

## Mandatory Instructions

- **Do not implement anything.** Do not run scripts. Rewrite the plan only.
- **Do not expand scope** beyond the 4 sessions + invariants.
- **Read every file in Section 6 before writing.** Your decisions depend on understanding the current code.
- **Do not put your analysis into the ROADMAP.md file.** Only markdown content.
- **All assumptions you make must be stated in your stdout analysis** (in the Decision Points section), so the reviewer can verify or override them.
