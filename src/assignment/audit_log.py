"""Correlated, framework-agnostic audit logging for VinBank."""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AuditLogPlugin:
    """Record sanitized request decisions for forensic replay."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        request_id = request_id or f"REQ-{uuid.uuid4().hex[:12].upper()}"
        self._open[request_id] = {
            "request_id": request_id,
            "user_id": user_id,
            "input": text,
            "input_at": utc_now_iso(),
            "_started": time.monotonic(),
        }
        return request_id

    def record_output(self, *, user_id: str, text: str, blocked: bool = False,
                      layer: str | None = None, request_id: str | None = None):
        request_id = request_id or f"REQ-{uuid.uuid4().hex[:12].upper()}"
        row = self._open.pop(request_id, {
            "request_id": request_id, "user_id": user_id, "input": None,
            "input_at": None, "_started": time.monotonic(),
        })
        started = row.pop("_started")
        row.update({
            "output": text,
            "output_at": utc_now_iso(),
            "blocked": bool(blocked),
            "layer": layer,
            "latency_ms": round((time.monotonic() - started) * 1000, 3),
        })
        self.logs.append(row)
        return row

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.logs, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
