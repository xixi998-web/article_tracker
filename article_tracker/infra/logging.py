from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class RunLog:
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_s: float = 0.0
    sources: Dict[str, int] = field(default_factory=dict)
    dedup: Dict[str, int] = field(default_factory=dict)
    screening: Dict[str, int] = field(default_factory=dict)
    enrichment: Dict[str, int] = field(default_factory=dict)
    output: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    _start: float = field(default_factory=time.time, repr=False)

    def finish(self) -> None:
        self.duration_s = round(time.time() - self._start, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "duration_s": self.duration_s,
            "sources": self.sources,
            "dedup": self.dedup,
            "screening": self.screening,
            "enrichment": self.enrichment,
            "output": self.output,
            "errors": self.errors,
        }

    def save(self, path: str | Path) -> None:
        self.finish()
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
