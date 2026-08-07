"""Monitoring counters and security alert thresholds."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Alert:
    metric: str
    value: float
    threshold: float
    message: str


@dataclass
class MonitoringAlert:
    block_rate_threshold: float = 0.5
    rate_limit_hit_threshold: int = 5
    judge_fail_rate_threshold: float = 0.3
    alerts: list[Alert] = field(default_factory=list)
    total_requests: int = 0
    blocked_requests: int = 0
    rate_limit_hits: int = 0
    judge_checks: int = 0
    judge_fails: int = 0

    def check_metrics(self) -> list[Alert]:
        self.alerts.clear()
        snapshot = self.snapshot()
        checks = [
            ("block_rate", snapshot["block_rate"], self.block_rate_threshold,
             "High request block rate may indicate an active attack."),
            ("rate_limit_hits", self.rate_limit_hits, self.rate_limit_hit_threshold,
             "Repeated rate-limit hits may indicate flooding or cost abuse."),
            ("judge_fail_rate", snapshot["judge_fail_rate"], self.judge_fail_rate_threshold,
             "LLM judge failures exceed the safe operating threshold."),
        ]
        for metric, value, threshold, message in checks:
            if value >= threshold and value > 0:
                self.alerts.append(Alert(metric, value, threshold, message))
        return list(self.alerts)

    def export_json(self, filepath: str = "outputs/metrics.json"):
        self.check_metrics()
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")
        return path

    def snapshot(self) -> dict:
        block_rate = self.blocked_requests / self.total_requests if self.total_requests else 0.0
        judge_fail_rate = self.judge_fails / self.judge_checks if self.judge_checks else 0.0
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": block_rate,
            "rate_limit_hits": self.rate_limit_hits,
            "judge_checks": self.judge_checks,
            "judge_fails": self.judge_fails,
            "judge_fail_rate": judge_fail_rate,
            "alerts": [asdict(a) for a in self.alerts],
        }
