# Launchd Setup — Traderie Snapshot Collection

## ⚠️ Already Installed

This job is already installed and running on this machine. **Default next-session action is inspect only.**

```bash
# Inspect state (safe — read only)
launchctl print gui/$(id -u)/com.buddy.traderie.snapshot-traderie

# Check label exists
launchctl list | grep com.buddy.traderie

# View logs
tail -n 50 logs/launchd/snapshot-traderie.out.log
tail -n 50 logs/launchd/snapshot-traderie.err.log
```

**Do not** run `bootstrap`, `bootout`, `kickstart`, `unload`, `remove`, or `restart` unless you are explicitly asked to repair or modify the job.

Do not touch any launchd label outside `com.buddy.traderie.*`.

---

## Namespace

All labels use the `com.buddy.traderie.*` namespace.

| Label | Purpose |
|---|---|
| `com.buddy.traderie.snapshot-traderie` | Collect Traderie completed-trade snapshots for all 4 segments |

## Why These Times

Existing `com.buddy.*` jobs run between 03:00–03:30 daily (WGU-Reddit, GPT-Email, IVY).
The four snapshot times (05:00, 11:00, 17:00, 23:00) avoid this window entirely.

The 6-hour cadence matches the Traderie rolling ~7-hour window: 4 snapshots/day
ensure no data is lost between cycles.

## Files

| File | Purpose |
|---|---|
| `launchd/com.buddy.traderie.snapshot-traderie.plist` | launchd job definition |
| `scripts/run_traderie_snapshot_launchd.sh` | Bash runner with lockfile |
| `logs/launchd/snapshot-traderie.out.log` | stdout |
| `logs/launchd/snapshot-traderie.err.log` | stderr |
| `.run/locks/snapshot-traderie.lock` | Overlap-prevention lock |

## Install

```bash
cp launchd/com.buddy.traderie.snapshot-traderie.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist
```

## Test (run immediately, regardless of schedule)

```bash
launchctl kickstart -k gui/$(id -u)/com.buddy.traderie.snapshot-traderie
```

## Status

```bash
launchctl print gui/$(id -u)/com.buddy.traderie.snapshot-traderie
```

## Uninstall

```bash
launchctl bootout gui/$(id -u)/com.buddy.traderie.snapshot-traderie
rm ~/Library/LaunchAgents/com.buddy.traderie.snapshot-traderie.plist
```

## Warnings

- Never run broad `launchctl unload`, `launchctl remove`, or `launchctl bootout`
  commands without the full label path. They can disable unrelated jobs.
- Never touch labels outside `com.buddy.traderie.*`.
- Always uninstall cleanly via the commands above before modifying the plist.

## Overlap Protection

Overlap protection uses `mkdir` (atomic on macOS) on the lock directory
`.run/locks/snapshot-traderie.lock`. If a run is still in progress when
the next scheduled time arrives, `mkdir` fails and the second run exits
immediately. The lock directory is removed automatically when the first
run finishes.
