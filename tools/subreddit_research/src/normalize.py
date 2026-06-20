from __future__ import annotations

from typing import Any, Dict


def normalize_submission(submission) -> Dict[str, Any]:
    subreddit_obj = getattr(submission, "subreddit", None)
    subreddit_name = getattr(subreddit_obj, "display_name", "") if subreddit_obj else ""
    author_obj = getattr(submission, "author", None)
    author_name = getattr(author_obj, "name", None) if author_obj else None
    permalink = getattr(submission, "permalink", "") or ""
    if permalink and not permalink.startswith("http"):
        permalink = "https://www.reddit.com" + permalink
    return {
        "submission_id": getattr(submission, "id", "") or "",
        "subreddit_name": subreddit_name,
        "author_name": author_name,
        "title": getattr(submission, "title", "") or "",
        "selftext": getattr(submission, "selftext", "") or "",
        "created_utc": float(getattr(submission, "created_utc", 0.0) or 0.0),
        "score": int(getattr(submission, "score", 0) or 0),
        "num_comments": int(getattr(submission, "num_comments", 0) or 0),
        "over_18": bool(getattr(submission, "over_18", False)),
        "permalink": permalink,
        "is_self": bool(getattr(submission, "is_self", False)),
        "url": getattr(submission, "url", "") or "",
        "post_hint": getattr(submission, "post_hint", None),
        "url_overridden_by_dest": getattr(submission, "url_overridden_by_dest", "") or "",
        "is_gallery": bool(getattr(submission, "is_gallery", False)),
        "gallery_data": getattr(submission, "gallery_data", None),
        "media_metadata": getattr(submission, "media_metadata", None),
        "preview": getattr(submission, "preview", None),
    }


def normalize_comment(comment, submission_id: str) -> Dict[str, Any]:
    sr_obj = getattr(comment, "subreddit", None)
    sr_name = getattr(sr_obj, "display_name", "") if sr_obj else ""
    author_obj = getattr(comment, "author", None)
    author_name = getattr(author_obj, "name", None) if author_obj else None
    permalink = getattr(comment, "permalink", "") or ""
    if permalink and not permalink.startswith("http"):
        permalink = "https://www.reddit.com" + permalink
    body = getattr(comment, "body", "") or ""
    return {
        "comment_id": getattr(comment, "id", "") or "",
        "submission_id": submission_id,
        "parent_id": getattr(comment, "parent_id", None),
        "subreddit_name": sr_name,
        "author_name": author_name,
        "created_utc": float(getattr(comment, "created_utc", 0.0) or 0.0),
        "score": int(getattr(comment, "score", 0) or 0),
        "body": body,
        "permalink": permalink,
        "is_submitter": bool(getattr(comment, "is_submitter", False)),
        "depth": int(getattr(comment, "depth", 0) or 0),
    }
