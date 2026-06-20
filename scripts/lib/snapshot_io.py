"""Shared snapshot I/O for parser pipelines.

Every parser should call:
  1. write_raw_snapshot()   — raw API/parser response
  2. write_normalized_snapshot()  — observations list
  3. append_history()       — dedup'd append to JSONL

Paths:
  Raw:        data/snapshots/raw/<source>/<YYYYMMDD_HHMMSS>/response.json
  Normalized: data/snapshots/normalized/<source>/<YYYYMMDD_HHMMSS>.json
  History:    data/history/<source>/<dataset>.jsonl
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def timestamped_dir(base_path: str, source: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    d = Path(base_path) / source / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_raw_snapshot(data, source: str) -> Path:
    base = ROOT_DIR / "data" / "snapshots" / "raw"
    d = timestamped_dir(str(base), source)
    path = d / "response.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  [snapshot] raw: {path}")
    return path


def write_normalized_snapshot(observations: list, source: str) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = ROOT_DIR / "data" / "snapshots" / "normalized" / source
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{ts}.json"
    payload = {
        "source": source,
        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "observation_count": len(observations),
        "observations": observations,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  [snapshot] normalized: {path}")
    return path


def append_history(source: str, dataset: str, observations: list) -> Path:
    base = ROOT_DIR / "data" / "history" / source
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{dataset}.jsonl"

    seen = load_history_keys(source, dataset)
    written = 0
    with open(path, "a") as f:
        for obs in observations:
            key = observation_key(obs)
            if key in seen:
                continue
            seen.add(key)
            record = {
                "_observation_key": key,
                "_content_hash": content_hash(obs),
                "_captured_at": obs.get("captured_at"),
                **obs,
            }
            f.write(json.dumps(record, default=str) + "\n")
            written += 1
    print(f"  [history] appended {written} new to {path} ({len(seen)} total unique keys)")
    return path


def content_hash(obj) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def observation_key(obs: dict) -> str:
    parts = [
        str(obs.get("source_slug", "")),
        str(obs.get("item_name", "")),
        str(obs.get("price", obs.get("price_usd", ""))),
        str(obs.get("captured_at", "")),
        str(obs.get("product_id", "")),
    ]
    return "::".join(parts)


def load_history_keys(source: str, dataset: str) -> set:
    path = ROOT_DIR / "data" / "history" / source / f"{dataset}.jsonl"
    if not path.exists():
        return set()
    keys = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                key = record.get("_observation_key")
                if key:
                    keys.add(key)
            except json.JSONDecodeError:
                continue
    return keys
