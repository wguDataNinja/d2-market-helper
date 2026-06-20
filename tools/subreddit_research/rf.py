#!/usr/bin/env python3
"""
rf.py — subreddit_research CLI

Usage:
  python rf.py fetch posts --subreddits subA subB --sort top --limit 500
  python rf.py browse --input data/submissions_*.jsonl
  python rf.py fetch comments --candidates data/candidates_*.jsonl --mode default
  python rf.py export --input data/comments/ --format markdown

Commands:
  fetch posts      Fetch subreddit submissions (Phase 1)
  browse           Interactive post selection for comment fetch (Phase 2)
  fetch comments   Fetch comment trees for selected posts (Phase 3, HITL-gated)
  export           Export fetched data for LLM consumption (Phase 4)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.config import EnvConfig


def cmd_fetch_posts(args) -> None:
    from src import fetch_posts

    cfg = EnvConfig(env_path=args.env_file)
    fetch_posts.run(
        cfg=cfg,
        subreddits=args.subreddits,
        sort=args.sort,
        time_filter=args.time_filter,
        limit=args.limit,
        query=args.query,
        run_name=args.run_name,
        sleep_subreddit=args.sleep_subreddit,
        sleep=args.sleep,
        batch_size=args.batch_size,
    )


def cmd_browse(args) -> None:
    from src import browse

    cfg = EnvConfig(env_path=args.env_file)
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input not found: {input_path}")
        sys.exit(1)
    browse.run(cfg=cfg, input_path=input_path, top=args.top)


def cmd_fetch_comments(args) -> None:
    from src import fetch_comments

    cfg = EnvConfig(env_path=args.env_file)
    candidates_path = Path(args.candidates)
    if not candidates_path.exists():
        print(f"Candidates not found: {candidates_path}")
        sys.exit(1)
    fetch_comments.run(
        cfg=cfg,
        candidates_path=candidates_path,
        mode=args.mode,
        sleep=args.sleep,
        run_name=args.run_name,
    )


def cmd_export(args) -> None:
    from src import export

    cfg = EnvConfig(env_path=args.env_file)
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    export.run(
        cfg=cfg,
        input_path=input_path,
        fmt=args.format,
        cap=args.cap,
        output_path=output_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="subreddit_research — portable Reddit data collection tool")
    parser.add_argument("--env-file", dest="env_file", default=None, help="Path to .env file")
    sub = parser.add_subparsers(dest="command")

    # fetch
    fetch_parser = sub.add_parser("fetch")
    fetch_sub = fetch_parser.add_subparsers(dest="fetch_command")

    fp = fetch_sub.add_parser("posts", help="Fetch subreddit submissions")
    fp.add_argument("--subreddits", nargs="+", required=True, help="Subreddit names (space-separated)")
    fp.add_argument("--sort", choices=["new", "top", "hot", "rising", "controversial"], default="new")
    fp.add_argument("--time-filter", choices=["hour", "day", "week", "month", "year", "all"], default="all")
    fp.add_argument("--limit", type=int, default=1000)
    fp.add_argument("--query", default=None, help="Keyword search within subreddit(s)")
    fp.add_argument("--run-name", default=None)
    fp.add_argument("--sleep", type=float, default=0.0, help="Seconds between request batches within a subreddit")
    fp.add_argument("--batch-size", type=int, default=100, help="Items per request batch (max 100)")
    fp.add_argument("--sleep-subreddit", type=float, default=1.0, help="Seconds between subreddits")

    fc = fetch_sub.add_parser("comments", help="Fetch comment trees (HITL-gated)")
    fc.add_argument("--candidates", required=True, help="Candidates JSONL from browse command")
    fc.add_argument("--mode", choices=["top", "default", "full"], default="default",
                    help="top=top-level only, default=single replace_more, full=full tree")
    fc.add_argument("--sleep", type=float, default=1.0, help="Seconds between submissions")
    fc.add_argument("--run-name", default=None)

    # browse
    bp = sub.add_parser("browse", help="Interactive post selection for comment fetch")
    bp.add_argument("--input", required=True, help="Submissions JSONL file")
    bp.add_argument("--top", type=int, default=0, help="Show only top N by score (0=all)")

    # export
    ep = sub.add_parser("export", help="Export data for LLM consumption")
    ep.add_argument("--input", required=True, help="Comment tree file or directory")
    ep.add_argument("--format", choices=["markdown", "jsonl", "txt"], default="markdown")
    ep.add_argument("--cap", type=int, default=0, help="Max trees to export (0=all)")
    ep.add_argument("--output", default=None, help="Output path (default: data/llm_exports/)")

    args = parser.parse_args()

    if args.command == "fetch":
        if args.fetch_command == "posts":
            cmd_fetch_posts(args)
        elif args.fetch_command == "comments":
            cmd_fetch_comments(args)
        else:
            print("fetch requires a subcommand: posts | comments")
    elif args.command == "browse":
        cmd_browse(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
