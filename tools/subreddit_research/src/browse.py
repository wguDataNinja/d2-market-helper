from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from .config import EnvConfig


PAGE_SIZE = 20


def load_posts(path: Path) -> List[Dict[str, Any]]:
    posts: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                posts.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return posts


def format_ts(ts: float) -> str:
    return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).strftime("%Y-%m-%d")


def truncate(s: str, max_len: int = 60) -> str:
    s = s.replace("\n", " ").replace("\r", "")
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def show_page(posts: List[Dict[str, Any]], page: int, selected: Set[int]) -> None:
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, len(posts))
    print()
    print(f"  Posts {start + 1}-{end} of {len(posts)}  (selected: {len(selected)})")
    print(f"  {'#':>4} {'score':>5} {'cmts':>4} {'date':>10}  {'author':>18}  title")
    print(f"  {'-'*4} {'-'*5} {'-'*4} {'-'*10}  {'-'*18}  {'-'*40}")
    for i in range(start, end):
        p = posts[i]
        idx = i + 1
        marker = ">" if idx in selected else " "
        score = p.get("score", 0)
        nc = p.get("num_comments", 0)
        date = format_ts(p.get("created_utc", 0))
        author = (p.get("author_name") or "[deleted]")[:18]
        title = truncate(p.get("title", ""), 50)
        print(f"  {marker}{idx:>3} {score:>5} {nc:>4} {date:>10}  {author:>18}  {title}")
    print()


def run(cfg: EnvConfig, input_path: Path, top: int) -> None:
    posts = load_posts(input_path)
    if not posts:
        print("No posts loaded.")
        return

    if top and top < len(posts):
        posts = sorted(posts, key=lambda p: -(p.get("score", 0) or 0))[:top]

    selected: Set[int] = set()
    page = 0
    max_page = max(0, (len(posts) - 1) // PAGE_SIZE)

    print()
    print("Interactive post browser")
    print("========================")
    print(f"  Input: {input_path}")
    print(f"  Total posts: {len(posts)}")
    if top:
        print(f"  Showing top {top} by score")
    print()

    while True:
        show_page(posts, page, selected)
        n_start = page * PAGE_SIZE + 1
        n_end = min((page + 1) * PAGE_SIZE, len(posts))
        print(f"  Page {page + 1}/{max_page + 1} (posts {n_start}-{n_end})")
        print()
        print("  Commands:")
        print("    n          next page")
        print("    p          previous page")
        print("    s <N>      toggle selection of post N (e.g. s 5)")
        print("    r <N-M>    toggle range of posts (e.g. r 5-12)")
        print("    a          select all on this page")
        print("    c          clear all selections")
        print("    l          list current selections")
        print("    done       write selections & exit")
        print("    q          quit without saving")
        print()

        try:
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "n":
            if page < max_page:
                page += 1
        elif cmd == "p":
            if page > 0:
                page -= 1
        elif cmd == "s":
            try:
                n = int(parts[1])
                if 1 <= n <= len(posts):
                    if n in selected:
                        selected.remove(n)
                    else:
                        selected.add(n)
            except (IndexError, ValueError):
                print("  Usage: s <number>")
        elif cmd == "r":
            try:
                lo, hi = parts[1].split("-")
                lo, hi = int(lo), int(hi)
                for n in range(lo, hi + 1):
                    if 1 <= n <= len(posts):
                        if n in selected:
                            selected.remove(n)
                        else:
                            selected.add(n)
            except (IndexError, ValueError):
                print("  Usage: r <N-M>")
        elif cmd == "a":
            for n in range(n_start, n_end + 1):
                selected.add(n)
        elif cmd == "c":
            selected.clear()
        elif cmd == "l":
            if selected:
                sorted_sel = sorted(selected)
                for n in sorted_sel:
                    p = posts[n - 1]
                    print(f"    {n}: {p.get('title', '')[:60]}")
            else:
                print("  No posts selected.")
        elif cmd == "done":
            if not selected:
                print("  No posts selected. Nothing to write.")
                continue
            ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
            out_path = cfg.data_dir / f"candidates_{ts}.jsonl"
            written = 0
            with out_path.open("w", encoding="utf-8") as f:
                for n in sorted(selected):
                    rec = posts[n - 1]
                    record = {
                        "submission_id": rec.get("submission_id", ""),
                        "subreddit_name": rec.get("subreddit_name", ""),
                        "title": rec.get("title", ""),
                        "author_name": rec.get("author_name"),
                        "score": rec.get("score", 0),
                        "num_comments": rec.get("num_comments", 0),
                        "created_utc": rec.get("created_utc", 0),
                        "permalink": rec.get("permalink", ""),
                    }
                    json.dump(record, f)
                    f.write("\n")
                    written += 1
            print(f"\n  Selected {written} posts")
            print(f"  Output: {out_path}")
            return
        elif cmd == "q":
            print("  Quit without saving.")
            return
        else:
            print("  Unknown command. Type h for help.")

    print("  Exited without saving.")
