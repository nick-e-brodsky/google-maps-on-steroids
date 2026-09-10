"""Resumable progress tracking, keyed by the place's Google Maps URL
(falls back to Title if URL is missing). Committed to the repo so progress
survives across sessions/containers - reruns only touch new or failed rows.
"""

import json
import os

MAX_RETRY_ATTEMPTS = 3


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(tmp_path, path)


def key_for(title: str, url: str) -> str:
    return url.strip() if url and url.strip() else f"title:{title.strip()}"


def should_process(record: dict | None, retry_failed: bool) -> bool:
    if record is None:
        return True
    if record.get("status") == "success":
        return False
    # status == "failed"
    if not retry_failed:
        return False
    return record.get("attempts", 0) < MAX_RETRY_ATTEMPTS
