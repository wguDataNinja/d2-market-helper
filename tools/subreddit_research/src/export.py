from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import EnvConfig


def load_comment_tree(path: Path) -> Optional[Dict[str, Any]]:
    submission = None
    comments: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "submission":
                submission = obj
            elif obj.get("type") == "comment":
                comments.append(obj)
    if submission is None:
        return None
    return {"submission": submission, "comments": comments}


def collapse_body(body: str) -> str:
    s = (body or "").strip()
    if not s:
        return "[empty]"
    return s


def export_markdown(tree: Dict[str, Any]) -> str:
    sub = tree["submission"]
    comments = sorted(tree["comments"], key=lambda c: (c.get("depth", 0), c.get("created_utc", 0)))
    op_author = sub.get("author_name")
    lines: List[str] = []
    lines.append("# Submission")
    lines.append("")
    lines.append(f"**ID:** {sub.get('submission_id', '')}")
    lines.append(f"**Subreddit:** r/{sub.get('subreddit_name', '')}")
    lines.append(f"**Author:** {sub.get('author_name') or '[deleted]'}")
    lines.append(f"**Score:** {sub.get('score', 0)}")
    lines.append(f"**Comments:** {sub.get('num_comments', 0)}")
    lines.append(f"**Posted:** {sub.get('created_utc', '')}")
    lines.append(f"**Permalink:** {sub.get('permalink', '')}")
    lines.append("")
    lines.append("## Title")
    lines.append("")
    lines.append((sub.get("title") or "").strip() or "[empty]")
    lines.append("")
    lines.append("## Selftext")
    lines.append("")
    st = collapse_body(sub.get("selftext", ""))
    lines.append(st)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Comments")
    lines.append("")
    for c in comments:
        depth = int(c.get("depth", 0) or 0)
        indent = "  " * depth
        author = c.get("author_name") or "[deleted]"
        score = c.get("score", 0)
        op_flag = " (OP)" if op_author and c.get("author_name") == op_author else ""
        body = collapse_body(c.get("body", ""))
        lines.append(f"{indent}**{author}** score={score}{op_flag}")
        for line in body.splitlines():
            lines.append(f"{indent}  {line}")
        lines.append("")
    lines.append("---")
    lines.append(f"*{len(comments)} comments*")
    return "\n".join(lines)


def export_jsonl(tree: Dict[str, Any]) -> str:
    lines: List[str] = []
    sub = tree["submission"]
    lines.append(json.dumps({"type": "submission", **sub}))
    for c in tree["comments"]:
        lines.append(json.dumps({"type": "comment", **c}))
    return "\n".join(lines)


def export_txt(tree: Dict[str, Any]) -> str:
    sub = tree["submission"]
    comments = sorted(tree["comments"], key=lambda c: (c.get("depth", 0), c.get("created_utc", 0)))
    op_author = sub.get("author_name")
    lines: List[str] = []
    lines.append(f"SUBMISSION: {sub.get('title', '')}")
    lines.append(f"Author: {sub.get('author_name') or '[deleted]'}  Score: {sub.get('score', 0)}  Comments: {sub.get('num_comments', 0)}")
    lines.append(f"Link: {sub.get('permalink', '')}")
    lines.append("")
    st = collapse_body(sub.get("selftext", ""))
    if st != "[empty]":
        lines.append(st)
        lines.append("")
    lines.append("--- COMMENTS ---")
    lines.append("")
    for c in comments:
        depth = int(c.get("depth", 0) or 0)
        indent = "  " * depth
        author = c.get("author_name") or "[deleted]"
        op_mark = " [OP]" if op_author and c.get("author_name") == op_author else ""
        body = collapse_body(c.get("body", ""))
        lines.append(f"{indent}{author}{op_mark} (score: {c.get('score', 0)})")
        for line in body.splitlines():
            lines.append(f"{indent}  {line}")
        lines.append("")
    return "\n".join(lines)


FORMATTERS = {
    "markdown": export_markdown,
    "jsonl": export_jsonl,
    "txt": export_txt,
}
FORMAT_EXT = {
    "markdown": "md",
    "jsonl": "jsonl",
    "txt": "txt",
}


def run(
    cfg: EnvConfig,
    input_path: Path,
    fmt: str,
    cap: int,
    output_path: Optional[Path],
) -> None:
    if fmt not in FORMATTERS:
        print(f"Unknown format: {fmt}. Options: {', '.join(FORMATTERS.keys())}")
        return

    if input_path.is_dir():
        tree_files = sorted(input_path.glob("*.jsonl"))
    elif input_path.is_file():
        tree_files = [input_path]
    else:
        print(f"Not found: {input_path}")
        return

    if not tree_files:
        print("No comment tree files found.")
        return

    if cap and len(tree_files) > cap:
        tree_files = tree_files[:cap]

    generate = FORMATTERS[fmt]
    ext = FORMAT_EXT[fmt]

    if len(tree_files) == 1:
        tree = load_comment_tree(tree_files[0])
        if tree is None:
            print(f"No valid tree in {tree_files[0]}")
            return
        output = generate(tree)
        if output_path:
            output_path.write_text(output, encoding="utf-8")
            print(f"Written {fmt} export to {output_path}")
        else:
            print(output)
        return

    out_dir = output_path or (cfg.data_dir / "llm_exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")

    combined = []
    for fpath in tree_files:
        tree = load_comment_tree(fpath)
        if tree is None:
            continue
        combined.append(tree)

    if fmt == "jsonl":
        out_path = out_dir / f"llm_export_{timestamp}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for tree in combined:
                sub = tree["submission"]
                f.write(json.dumps({"type": "submission", **sub}) + "\n")
                for c in tree["comments"]:
                    f.write(json.dumps({"type": "comment", **c}) + "\n")
        print(f"Written combined JSONL to {out_path}")
    else:
        for i, tree in enumerate(combined):
            sid = tree["submission"].get("submission_id", f"tree_{i}")
            out_path = out_dir / f"llm_export_{timestamp}_{sid}.{ext}"
            out_path.write_text(generate(tree), encoding="utf-8")
            print(f"Written {fmt} export to {out_path}")
