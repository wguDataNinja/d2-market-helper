#!/usr/bin/env python3
"""collection_status.py — Inspect-only operational health report.

Reads local files only. No network requests. No scrapers.
Reports history row counts, snapshot freshness, product ages, and log health.
"""

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Runtime paths that may not exist (ignored in git)
HISTORY_DIR = ROOT_DIR / "data" / "history" / "traderie"
SNAPSHOTS_DIR = ROOT_DIR / "data" / "snapshots" / "normalized"
LOGS_DIR = ROOT_DIR / "logs" / "launchd"
LOCK_FILE = ROOT_DIR / ".run" / "locks" / "snapshot-traderie.lock"
PRODUCTS_DIR = ROOT_DIR / "data" / "products"

SEGMENTS = ["pc_sc_l", "pc_sc_nl", "pc_hc_l", "pc_hc_nl"]
NOW = datetime.now(timezone.utc)

STALE_HOURS = 12  # warn if latest snapshot is older than this


def safe_read_jsonl(path: Path) -> tuple[list[dict], int]:
    """Read JSONL lines, return (parsed_rows, bad_line_count)."""
    rows = []
    bad = 0
    if not path.exists():
        return rows, 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return rows, bad


def safe_read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def segment_status(row_count: int, latest_ts: str | None) -> str:
    if row_count == 0:
        return "missing"
    if latest_ts:
        try:
            dt = datetime.fromisoformat(latest_ts.replace("Z", "+00:00"))
            hours_ago = (NOW - dt).total_seconds() / 3600
            if hours_ago > STALE_HOURS:
                return "stale"
        except (ValueError, TypeError):
            pass
    if row_count < 100:
        return "thin"
    return "ok"


def collect_traderie_segments() -> list[dict]:
    results = []
    for seg in SEGMENTS:
        info = {"segment": seg, "history_path": None, "row_count": 0,
                "bad_lines": 0, "unique_ids": 0, "latest_seen": None,
                "latest_snapshot_path": None, "latest_snapshot_mtime": None,
                "status": "missing"}

        # History file
        hist_path = HISTORY_DIR / seg / f"completed_trades_{seg}.jsonl"
        if hist_path.exists():
            info["history_path"] = str(hist_path.relative_to(ROOT_DIR))
            rows, bad = safe_read_jsonl(hist_path)
            info["row_count"] = len(rows)
            info["bad_lines"] = bad
            ids = set()
            for r in rows:
                lid = r.get("listing_id")
                if lid:
                    ids.add(str(lid))
            info["unique_ids"] = len(ids)
            timestamps = []
            for r in rows:
                t = r.get("updated_at") or r.get("sold_at_relative") or r.get("captured_at")
                if t:
                    timestamps.append(t)
            if timestamps:
                info["latest_seen"] = max(timestamps)

        # Latest snapshot
        snap_dir = SNAPSHOTS_DIR / "traderie" / seg
        if snap_dir.exists():
            files = sorted(snap_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                latest = files[0]
                info["latest_snapshot_path"] = str(latest.relative_to(ROOT_DIR))
                info["latest_snapshot_mtime"] = datetime.fromtimestamp(
                    latest.stat().st_mtime, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

        info["status"] = segment_status(info["row_count"], info["latest_seen"])
        results.append(info)
    return results


def collect_products() -> list[dict]:
    results = []
    product_files = [
        "in_game_rune_values.json",
        "traderie_tools_prices.json",
        "external_cash_prices.sample.json",
        "rune_prices_legacy.json",
    ]
    for fname in product_files:
        path = PRODUCTS_DIR / fname
        info = {"product": fname, "path": str(path.relative_to(ROOT_DIR)),
                "exists": False, "schema_version": None,
                "generated_at": None, "source_window_label": None,
                "segments": None, "observations": None}
        data = safe_read_json(path)
        if data is None:
            results.append(info)
            continue
        info["exists"] = True
        info["schema_version"] = data.get("schema_version")
        info["generated_at"] = data.get("product_generated_at") or data.get("generated_at")
        info["source_window_label"] = data.get("source_window_label")

        if "segments" in data and isinstance(data["segments"], dict):
            info["segments"] = len(data["segments"])
            first_seg = next(iter(data["segments"].values()), {})
            if "runes" in first_seg:
                info["observations"] = sum(len(s.get("runes", {})) for s in data["segments"].values())
            elif isinstance(first_seg, dict):
                # Flat format (rune_prices_legacy): keys are rune names
                total = sum(len(list(s.values())) for s in data["segments"].values()
                            if isinstance(s, dict))
                info["observations"] = total if total else None

        if "observations" in data and isinstance(data["observations"], list):
            info["observations"] = len(data["observations"])
        if "metadata" in data and isinstance(data["metadata"], dict):
            info["observations"] = data["metadata"].get("observation_count", info["observations"])
        if "sources" in data and isinstance(data["sources"], list):
            info["source_count"] = len(data["sources"])
            if not info["observations"]:
                info["observations"] = sum(s.get("observation_count", 0) for s in data["sources"])

        results.append(info)
    return results


def collect_cash_snapshots() -> list[dict]:
    results = []
    if not SNAPSHOTS_DIR.exists():
        return results
    for source_dir in sorted(SNAPSHOTS_DIR.iterdir()):
        if source_dir.name == "traderie" or not source_dir.is_dir():
            continue
        files = sorted(source_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        latest = files[0] if files else None
        info = {
            "source": source_dir.name,
            "latest_snapshot_path": str(latest.relative_to(ROOT_DIR)) if latest else None,
            "latest_snapshot_mtime": datetime.fromtimestamp(
                latest.stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
            "snapshot_count": len(files),
        }
        if latest:
            data = safe_read_json(latest)
            info["observation_count"] = len(data) if isinstance(data, list) else None
        results.append(info)
    return results


def collect_logs() -> dict:
    info = {"out_exists": False, "err_exists": False, "total_out_lines": 0,
            "total_err_lines": 0, "recent_timeout_count": 0,
            "last_out_lines": [], "last_err_lines": [], "summary": []}
    for fname in ("snapshot-traderie.out.log", "snapshot-traderie.err.log"):
        path = LOGS_DIR / fname
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if fname.endswith(".out.log"):
            info["out_exists"] = True
            info["total_out_lines"] = len(lines)
            info["last_out_lines"] = lines[-20:]
        else:
            info["err_exists"] = True
            info["total_err_lines"] = len(lines)
            timeout_lines = [l for l in lines if "ReadTimeout" in l]
            info["recent_timeout_count"] = len(timeout_lines)
            info["last_err_lines"] = lines[-20:]

    # Summarize
    if info["recent_timeout_count"] > 0:
        info["summary"].append(f"err.log: {info['recent_timeout_count']} ReadTimeout(s)")
    if LOCK_FILE.exists():
        info["summary"].append("stale lock file present at .run/locks/snapshot-traderie.lock (remove if no process running)")
    return info


def report_text(segments: list[dict], products: list[dict],
                cash_snaps: list[dict], logs: dict) -> str:
    lines = []
    lines.append("=" * 64)
    lines.append("D2R Market Helper — Collection Status")
    lines.append(f"Generated: {NOW.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("=" * 64)

    # Traderie segments
    lines.append("")
    lines.append("--- Traderie History by Segment ---")
    lines.append(f"{'Segment':<12} {'Status':<10} {'Rows':>8}  {'Unique IDs':>12}  {'Latest Seen':<25}  {'Latest Snapshot'}")
    lines.append("-" * 120)
    for s in segments:
        seen = s["latest_seen"][:19] if s["latest_seen"] else "—"
        snap = s["latest_snapshot_path"] or "—"
        lines.append(f"{s['segment']:<12} {s['status']:<10} {s['row_count']:>8}  {s['unique_ids']:>12}  {seen:<25}  {snap}")

    all_ok = all(s["status"] in ("ok", "thin") for s in segments)
    any_missing = any(s["status"] == "missing" for s in segments)
    any_stale = any(s["status"] == "stale" for s in segments)

    # Cash snapshots
    if cash_snaps:
        lines.append("")
        lines.append("--- Cash Source Snapshots ---")
        for cs in cash_snaps:
            mtime = cs["latest_snapshot_mtime"] or "—"
            obs = f" ({cs['observation_count']} obs)" if cs.get("observation_count") else ""
            lines.append(f"  {cs['source']:<12} {cs['snapshot_count']:>3} snapshots, latest: {mtime}{obs}")

    # Products
    lines.append("")
    lines.append("--- Products ---")
    for p in products:
        if not p["exists"]:
            lines.append(f"  {p['product']:<40} MISSING")
            continue
        gen = (p["generated_at"] or "?")[:19]
        sv = p["schema_version"] or "?"
        win = p["source_window_label"] or "—"
        obs = f", {p['observations']} obs" if p.get("observations") else ""
        segs = f", {p['segments']} segments" if p.get("segments") else ""
        lines.append(f"  {p['product']:<40} v{sv}{obs}{segs}  generated={gen}  window={win}")

    # Logs
    lines.append("")
    lines.append("--- Launchd Logs ---")
    if logs["out_exists"]:
        lines.append(f"  stdout: {logs['total_out_lines']} lines (last 20 shown below)")
        for l in logs["last_out_lines"][-10:]:
            lines.append(f"    {l}")
    if logs["err_exists"]:
        lines.append(f"  stderr: {logs['total_err_lines']} lines, {logs['recent_timeout_count']} ReadTimeout(s)")
        for l in logs["last_err_lines"][-5:]:
            if "ReadTimeout" in l or "ERROR" in l or "Traceback" in l:
                lines.append(f"    {l[:200]}")

    for s in logs["summary"]:
        lines.append(f"  NOTE: {s}")

    # Overall
    lines.append("")
    lines.append("--- Overall ---")
    if not logs["out_exists"]:
        lines.append("  WARNING: no launchd stdout log found (job may not have run yet)")
    if any_missing:
        lines.append("  WARNING: one or more segments have no history")
    if any_stale:
        lines.append("  WARNING: one or more segments have stale snapshots")
    if logs["recent_timeout_count"] > 0:
        lines.append("  WARNING: hardcore timeouts detected — 30s timeout + retry fix applied")
    if all_ok and logs["out_exists"]:
        lines.append("  STATUS: ok")
    else:
        lines.append("  STATUS: needs attention")
    lines.append("")
    return "\n".join(lines)


def report_json(segments: list[dict], products: list[dict],
                cash_snaps: list[dict], logs: dict) -> str:
    return json.dumps({
        "generated_at": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "traderie_segments": segments,
        "cash_snapshots": cash_snaps,
        "products": products,
        "logs": {
            "out_exists": logs["out_exists"],
            "err_exists": logs["err_exists"],
            "total_out_lines": logs["total_out_lines"],
            "total_err_lines": logs["total_err_lines"],
            "recent_timeout_count": logs["recent_timeout_count"],
            "summary": logs["summary"],
        },
        "lock_exists": LOCK_FILE.exists(),
    }, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(
        description="Collection status — inspect-only operational health report")
    parser.add_argument("--json", action="store_true",
                        help="Output machine-readable JSON")
    args = parser.parse_args()

    segments = collect_traderie_segments()
    products = collect_products()
    cash_snaps = collect_cash_snapshots()
    logs = collect_logs()

    if args.json:
        print(report_json(segments, products, cash_snaps, logs))
    else:
        print(report_text(segments, products, cash_snaps, logs))


if __name__ == "__main__":
    main()
