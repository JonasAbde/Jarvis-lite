"""history.py
Enkel håndtering af samtalehistorikken.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

HISTORY_DIR = Path("data/history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _today_file() -> Path:
    dt = datetime.now().strftime("%Y-%m-%d")
    return HISTORY_DIR / f"{dt}.json"


def append(user_text: str, assistant_text: str) -> None:
    """Tilføj en ny samtale-replik til dagens fil."""
    path = _today_file()
    data: List[Tuple[str, str]] = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = []
    data.append((user_text, assistant_text))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def last_n(n: int = 5) -> List[Tuple[str, str]]:
    """Hent de sidste *n* replikker fra dagens historik."""
    path = _today_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data[-n:]
    except json.JSONDecodeError:
        return [] 