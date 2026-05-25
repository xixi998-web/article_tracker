from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Set


class SeenStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return
        try:
            text = self.path.read_text(encoding="utf-8")
            self._data = json.loads(text) if text.strip() else {}
        except (json.JSONDecodeError, Exception):
            bak = self.path.with_suffix(".json.bak")
            shutil.copy2(self.path, bak)
            self._data = {}

    def has(self, key: str) -> bool:
        return key in self._data

    def mark(self, key: str, info: Any = None) -> None:
        self._data[key] = info or {}

    def keys(self) -> Set[str]:
        return set(self._data.keys())

    def merge(self, other: Dict[str, Any]) -> int:
        count = 0
        for k, v in other.items():
            if k not in self._data:
                self._data[k] = v
                count += 1
        return count

    def persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    @property
    def count(self) -> int:
        return len(self._data)
