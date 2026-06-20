from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import praw
import prawcore
from praw.models import MoreComments

from .config import EnvConfig, setup_logging
from .normalize import normalize_comment, normalize_submission


def load_candidates(path: Path) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                candidates.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return candidates


def fetch_tree(
    reddit: praw.Reddit,
    submission_id: str,
    mode: str,
    logger,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], int, Optional[str]]:
    try:
        submission = reddit.submission(id=submission_id)
        _ = submission.title
    except Exception as exc:
        return None, [], 0, f"Failed to load submission: {type(exc).__name__}: {exc}"

    reported_comments = int(getattr(submission, "num_comments", 0) or 0)

    try:
        if mode == "top":
            all_comments = list(submission.comments)
        elif mode == "default":
            submission.comments.replace_more(limit=0)
            all_comments = submission.comments.list()
        elif mode == "full":
            submission.comments.replace_more(limit=None)
            all_comments = submission.comments.list()
        else:
            return None, [], 0, f"Unknown mode: {mode}"
    except Exception as exc:
        return None, [], 0, f"Failed to expand comments: {type(exc).__name__}: {exc}"

    sub_rec = normalize_submission(submission)
    comments: List[Dict[str, Any]] = []
    skipped = 0
    for c in all_comments:
        if isinstance(c, MoreComments):
            skipped += 1
            continue
        try:
            rec = normalize_comment(c, submission_id)
            comments.append(rec)
        except Exception as exc:
            logger.warning("Skipping comment on %s: %s", submission_id, exc)
            skipped += 1

    logger.info(
        "Tree %s: mode=%s reported=%d written=%d skipped=%d",
        submission_id, mode, reported_comments, len(comments), skipped,
    )
    return sub_rec, comments, reported_comments, None


def run(
    cfg: EnvConfig,
    candidates_path: Path,
    mode: str,
    sleep: float,
    run_name: Optional[str],
) -> None:
    candidates = load_candidates(candidates_path)
    if not candidates:
        print("No candidates loaded.")
        return

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = (run_name or "fetch_comments").replace(" ", "_")
    run_id = f"{timestamp}_{slug}"
    logger, log_path = setup_logging(cfg.logs_dir, "fetch_comments", run_id)

    print()
    print("Comment fetch — approval required")
    print("=================================")
    print(f"Candidates: {len(candidates)}")
    print(f"Mode:       {mode}")
    print(f"Sleep:      {sleep}s between posts")
    print()
    print("Posts to fetch:")
    for i, c in enumerate(candidates, 1):
        title = (c.get("title") or "")[:70]
        author = c.get("author_name") or "[deleted]"
        score = c.get("score", 0)
        nc = c.get("num_comments", 0)
        sid = c.get("submission_id", "")
        print(f"  {i:>3}. [{nc:>4} cmts] {title}")
        print(f"       id={sid}  author={author}  score={score}")
    print()

    try:
        raw = input("Fetch comments for these posts? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        print("Aborted.")
        return

    if raw not in ("y", "yes"):
        print("Skipped.")
        return

    reddit = cfg.make_reddit()
    out_dir = cfg.data_dir / "comments"
    out_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    total_comments = 0

    for i, cand in enumerate(candidates, 1):
        sid = cand.get("submission_id", "")
        if not sid:
            logger.warning("Skipping candidate with no submission_id at index %d", i)
            continue

        if i > 1 and sleep > 0:
            logger.info("Sleeping %.1fs...", sleep)
            time.sleep(sleep)

        out_path = out_dir / f"comments_{sid}_{run_id}.jsonl"
        logger.info("(%d/%d) Fetching %s (mode=%s)", i, len(candidates), sid, mode)

        sub_rec, comments, reported, error = fetch_tree(reddit, sid, mode, logger)
        if error:
            logger.error("(%d/%d) Failed %s: %s", i, len(candidates), sid, error)
            results.append({"submission_id": sid, "status": "error", "error": error, "comments_written": 0})
            continue

        written = 0
        with out_path.open("w", encoding="utf-8") as f:
            json.dump({"type": "submission", **sub_rec}, f)
            f.write("\n")
            for c in comments:
                json.dump({"type": "comment", **c}, f)
                f.write("\n")
                written += 1

        total_comments += written
        logger.info("(%d/%d) Written %d comments for %s", i, len(candidates), written, sid)
        results.append({"submission_id": sid, "status": "ok", "comments_written": written, "reported": reported})

        print(f"  [{i}/{len(candidates)}] {sid}: {written} comments written (reported: {reported})")

    print()
    print("Fetch summary")
    print("-------------")
    print(f"Run ID: {run_id}")
    print(f"Mode: {mode}")
    print(f"Candidates: {len(candidates)}")
    ok_count = sum(1 for r in results if r["status"] == "ok")
    print(f"Succeeded: {ok_count}")
    print(f"Failed: {len(results) - ok_count}")
    print(f"Total comments written: {total_comments}")
    print(f"Output dir: {out_dir}")
    print(f"Log: {log_path}")
