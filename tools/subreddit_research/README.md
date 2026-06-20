# subreddit_research

Portable, ad-hoc Reddit research tool for by-subreddit data collection.

## Why this exists

A standalone extraction from the [Chivegate](https://github.com/anomalyco/chive-gate) methodological pattern. The two-phase fetch (posts first, comments second with a human-in-the-loop gate) keeps the Reddit API rate limit under control and ensures you never fetch comments for posts you don't actually need.

## Workflow

```
  Phase 1              Phase 2             Phase 3              Phase 4
  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
  │ fetch    │───>│ browse       │───>│ fetch        │───>│ export   │
  │ posts    │    │ (interactive)│    │ comments     │    │ for LLM  │
  │          │    │              │    │ (HITL gate)  │    │          │
  └──────────┘    └──────────────┘    └──────────────┘    └──────────┘
```

### Phase 1 — Fetch posts

```bash
python rf.py fetch posts \
  --subreddits KitchenConfidential \
  --sort top --time_filter year \
  --limit 500 \
  --run_name kc_top_year
```

Supports multiple subreddits, keyword search (`--query`), and all Reddit listing sorts.

Output: `data/submissions_<timestamp>.jsonl`

### Phase 2 — Browse and select (HITL)

```bash
python rf.py browse \
  --input data/submissions_20260614_120000.jsonl \
  --top 50
```

Interactive CLI: paginated post summaries, select by index/range, `done` to save. The `--top` flag shows only the highest-scored N posts for quick triage.

Output: `data/candidates_<timestamp>.jsonl`

### Phase 3 — Fetch comments (HITL-gated)

```bash
python rf.py fetch comments \
  --candidates data/candidates_20260614_121500.jsonl \
  --mode default \
  --sleep 1.0
```

Prints the full candidate list and waits for `y/N` approval before making any API calls. Three modes:

| Mode | Behavior | API calls |
|------|----------|-----------|
| `top` | Top-level comments only, no `replace_more` | 1 per post |
| `default` | Single `replace_more(limit=0)` pass | 1-2 per post |
| `full` | `replace_more(limit=None)` — full tree | Many per post |

Output: `data/comments/comments_<submission_id>_<run_id>.jsonl`

### Phase 4 — Export for LLM

```bash
python rf.py export \
  --input data/comments/ \
  --format markdown \
  --cap 10
```

Formats:
- `markdown` — threaded comment view with nesting, author, scores
- `jsonl` — flat combined JSONL
- `txt` — stripped plain text

## Setup

### 1. Reddit API credentials

Create a Reddit app at https://www.reddit.com/prefs/apps (script type). Then:

```bash
cp .env.example .env
```

Fill in `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and optionally `REDDIT_USER_AGENT`.

### 2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run

```bash
python rf.py --help
```

## Credentials

The `.env` file is gitignored. You can also share credentials across projects with `--env-file`:

```bash
python rf.py fetch posts --subreddits lego --limit 100 --env-file /path/to/shared/.env
```

## Safety features

| Concern | Mechanism |
|---------|-----------|
| API rate limits | 429 retry, `--sleep` flags, capped `--limit` |
| Accidental mass fetch | Phase 3 requires explicit `y/N` approval |
| Overwrite | All outputs are timestamped and append-safe |
| Credential exposure | `.env` gitignored, `--env-file` path never logged |
| Comment depth | `--mode` controls cost: `top` (1 call), `default` (balanced), `full` (expensive) |

## Data format

Universal JSONL (line-delimited JSON). See `data/README.md`.

## What this tool does NOT do

- No user history fetching
- No delta triage or "high signal" classification (that's your job — the tool just fetches)
- No LLM synthesis
- No canonical storage or doc editing
- No git operations

## Origin

Adapted from the [Chivegate](https://github.com/anomalyco/chive-gate) Reddit data pipeline. Replaces project-specific conventions with standalone portability.
