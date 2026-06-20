from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import praw
import prawcore

from .config import EnvConfig, setup_logging
from .normalize import normalize_submission


def load_existing_ids(path: str, id_field: str) -> Set[str]:
    ids: Set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                sid = obj.get(id_field)
                if sid:
                    ids.add(str(sid))
            except Exception:
                continue
    return ids


def iter_listing(
    sr,
    sort: str,
    time_filter: str,
    query: Optional[str],
    limit: int,
) -> Any:
    sort = sort.lower()
    if query:
        return sr.search(query=query, sort=sort, time_filter=time_filter, limit=limit)
    if sort == "new":
        return sr.new(limit=limit)
    if sort == "hot":
        return sr.hot(limit=limit)
    if sort == "rising":
        return sr.rising(limit=limit)
    if sort == "top":
        return sr.top(time_filter=time_filter, limit=limit)
    if sort == "controversial":
        return sr.controversial(time_filter=time_filter, limit=limit)
    raise ValueError(f"Unsupported sort: {sort}")


def fetch_subreddit_listing(
    reddit: praw.Reddit,
    subreddit_name: str,
    sort: str,
    time_filter: str,
    limit: int,
    query: Optional[str],
    sleep: float,
    batch_size: int,
) -> list[Any]:
    sr = reddit.subreddit(subreddit_name)
    generator = iter_listing(sr, sort, time_filter, query, limit)
    results: list[Any] = []
    count = 0
    for item in generator:
        results.append(item)
        count += 1
        if count % batch_size == 0 and sleep > 0 and count < limit:
            time.sleep(sleep)
    return results


def write_jsonl(
    records: List[Dict[str, Any]],
    out_path: Path,
    mode: str = "w",
) -> Tuple[int, int, Optional[float], Optional[float]]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids: Set[str] = set()
    existing_count = 0
    if mode == "a" and out_path.exists():
        existing_ids = load_existing_ids(str(out_path), "submission_id")
        existing_count = len(existing_ids)
    written = 0
    skipped = 0
    earliest: Optional[float] = None
    latest: Optional[float] = None
    with out_path.open(mode, encoding="utf-8") as f:
        for rec in records:
            sid = rec.get("submission_id", "")
            if sid and sid in existing_ids:
                skipped += 1
                continue
            json.dump(rec, f)
            f.write("\n")
            written += 1
            existing_ids.add(str(sid))
            ts = rec.get("created_utc")
            if isinstance(ts, (int, float)):
                tsf = float(ts)
                if earliest is None or tsf < earliest:
                    earliest = tsf
                if latest is None or tsf > latest:
                    latest = tsf
    return written, skipped, earliest, latest


def run(
    cfg: EnvConfig,
    subreddits: List[str],
    sort: str,
    time_filter: str,
    limit: int,
    query: Optional[str],
    run_name: Optional[str],
    sleep_subreddit: float,
    sleep: float = 0.0,
    batch_size: int = 100,
) -> None:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = (run_name or "fetch_posts").replace(" ", "_")
    run_id = f"{timestamp}_{slug}"
    logger, log_path = setup_logging(cfg.logs_dir, "fetch_posts", run_id)
    reddit = cfg.make_reddit()
    out_path = cfg.data_dir / f"submissions_{run_id}.jsonl"

    total_fetched = 0
    total_skipped = 0
    per_subreddit: List[Dict[str, Any]] = []

    for i, sub_name in enumerate(subreddits):
        if i > 0 and sleep_subreddit > 0:
            logger.info("Sleeping %.1fs before next subreddit...", sleep_subreddit)
            time.sleep(sleep_subreddit)
        logger.info(
            "Fetching r/%s  sort=%s time_filter=%s limit=%d query=%r",
            sub_name, sort, time_filter, limit, query,
        )
        try:
            posts = fetch_subreddit_listing(
                reddit=reddit,
                subreddit_name=sub_name,
                sort=sort,
                time_filter=time_filter,
                limit=limit,
                query=query,
                sleep=sleep,
                batch_size=batch_size,
            )
        except Exception as exc:
            logger.error("Failed fetching r/%s: %s %s", sub_name, type(exc).__name__, exc)
            per_subreddit.append({"subreddit": sub_name, "status": "error", "error": str(exc), "fetched": 0})
            continue
        records = []
        for p in posts:
            try:
                rec = normalize_submission(p)
                records.append(rec)
            except prawcore.exceptions.TooManyRequests:
                raise
            except Exception as exc:
                logger.warning("Skipping one item on r/%s: %s", sub_name, exc)
        sub_written, sub_skipped, sub_earliest, sub_latest = write_jsonl(records, out_path, mode="a")
        total_fetched += sub_written
        total_skipped += sub_skipped
        span = ""
        if sub_earliest is not None and sub_latest is not None:
            s_dt = dt.datetime.fromtimestamp(sub_earliest, tz=dt.timezone.utc)
            e_dt = dt.datetime.fromtimestamp(sub_latest, tz=dt.timezone.utc)
            span = f"{s_dt.isoformat()} to {e_dt.isoformat()}"
        logger.info(
            "r/%s: fetched=%d skipped=%d span=[%s]",
            sub_name, sub_written, sub_skipped, span,
        )
        per_subreddit.append({
            "subreddit": sub_name,
            "status": "ok",
            "fetched": sub_written,
            "skipped": sub_skipped,
            "earliest": sub_earliest,
            "latest": sub_latest,
        })

    print()
    print("Fetch summary")
    print("-------------")
    print(f"Run ID: {run_id}")
    if run_name:
        print(f"Run name: {run_name}")
    print(f"Sort: {sort}")
    print(f"Batch size: {batch_size}  Sleep between batches: {sleep}s")
    if query or sort in {"top", "controversial"}:
        print(f"Time filter: {time_filter}")
    if query:
        print(f"Query: {query}")
    print(f"Total fetched (new): {total_fetched}")
    print(f"Total skipped (dupes): {total_skipped}")
    print(f"Output: {out_path}")
    print(f"Log: {log_path}")
    print()
    for sr in per_subreddit:
        status = sr["status"]
        name = sr["subreddit"]
        if status == "ok":
            f = sr["fetched"]
            sk = sr["skipped"]
            print(f"  [{status}] r/{name}: {f} fetched, {sk} skipped")
        else:
            print(f"  [{status}] r/{name}: {sr.get('error', 'unknown')}")
