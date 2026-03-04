import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path(".cache")
VOCAB_CACHE_FILE = CACHE_DIR / "vocabs.json"


def save_vocab_cache(data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    with open(VOCAB_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_vocab_cache() -> dict | None:
    if VOCAB_CACHE_FILE.exists():
        with open(VOCAB_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None