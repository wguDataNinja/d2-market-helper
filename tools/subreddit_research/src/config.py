from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import praw


class EnvConfig:
    repo_root: Path
    data_dir: Path
    logs_dir: Path
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str

    def __init__(self, env_path: Optional[Path] = None):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.data_dir = self.repo_root / "data"
        self.logs_dir = self.repo_root / "logs"
        self._load_env(env_path or self.repo_root / ".env")
        self.reddit_client_id = os.environ["REDDIT_CLIENT_ID"]
        self.reddit_client_secret = os.environ["REDDIT_CLIENT_SECRET"]
        self.reddit_user_agent = os.environ.get(
            "REDDIT_USER_AGENT", "subreddit-research/0.1"
        )

    @staticmethod
    def _load_env(env_path: Path) -> None:
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except Exception:
            if env_path.exists():
                with env_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ.setdefault(key, value)

    def make_reddit(self) -> praw.Reddit:
        return praw.Reddit(
            client_id=self.reddit_client_id,
            client_secret=self.reddit_client_secret,
            user_agent=self.reddit_user_agent,
        )


def setup_logging(
    logs_dir: Path, run_slug: str, run_id: str
) -> Tuple[logging.Logger, Path]:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"{run_slug}_{run_id}.log"
    logger = logging.getLogger(f"{run_slug}_{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = logging.FileHandler(str(log_path))
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.info("Logging to %s", log_path)
    return logger, log_path
