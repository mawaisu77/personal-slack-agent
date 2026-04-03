from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ReplayTraceStore:
    """
    JSONL replay trace writer (T-045).
    One line per step with version metadata.
    """

    def __init__(self, root: str | Path = "var/replay") -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        task_id: str,
        step: int,
        payload: dict[str, Any],
        version: str = "v1",
    ) -> Path:
        p = self._root / f"{task_id}.jsonl"
        line = json.dumps(
            {"version": version, "step": step, "payload": payload},
            separators=(",", ":"),
        )
        with p.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        return p

    def read_trace_lines(self, task_id: str) -> list[dict[str, Any]]:
        """Load JSONL lines for replay / equivalence checks (T-050)."""
        p = self._root / f"{task_id}.jsonl"
        if not p.is_file():
            return []
        lines: list[dict[str, Any]] = []
        for raw in p.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            lines.append(json.loads(raw))
        return lines
