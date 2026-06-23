# AGENTS — D2R Market Helper Operating Contract

Default agent: `orchestrator`.

## Orchestrator

- Default entrypoint for all repo work
- May write only: `AGENTS.md`, `SESSION.md`, `LOG.md`, `logs/sessions/*.md`
- `SESSION.md` and `LOG.md` are NOT created during inspection-only tasks — only when starting real work or after meaningful work (respectively)
- Does not code, edit docs/source, run git, or edit agent config

## Subagent Assignment

| Task | Route to |
|------|----------|
| Source/docs edits, implementation, validation | `worker` |
| Git / dirty tree / clean tree / commit / staging | `git-steward` (objective: get tree clean safely) |
| Architecture/implementation roadmaps | `roadmap-planner` |
| Executable tasks from roadmap | `task-reviewer` |
| Agent config changes | `agent-manager` |

## Existing Repo Conventions

- Session closeouts: `research/memos/YYYY-MM-DD-*.md`
- State doc: `docs/PROJECT_MEMORY.md`
- Roadmap: `ROADMAP.md`
- Do not duplicate these — reference from orchestrator-owned files.

## Safety

- Never blend cash-market prices into in-game rune values
- Never merge economy segments (PC SC L, PC SC NL, PC HC L, PC HC NL)
- Do not run launchctl mutations unless explicitly asked
- Do not touch the external TraderieTools userscript repo unless explicitly asked
- Do not expose credentials from `tools/subreddit_research/.env`
