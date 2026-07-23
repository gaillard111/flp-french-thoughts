#!/usr/bin/env python3
"""
logger_compensator_adapter.py — Logging adapter for ConstraintCompensator.

Provides structured logging and metric export for the constraint compensation
layer. Designed for integration into observability pipelines (Prometheus,
WandB, MLflow) without exposing the underlying policy architecture.

This module contains no references to any specific framework, deployment,
or systemic purpose beyond general constrained generation monitoring.
"""

from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] compensator: %(message)s",
)
logger = logging.getLogger("compensator-adapter")


@dataclass
class CompensationEvent:
    """A single compensation event record for observability pipelines."""

    step_index: int
    mode: str
    latency_multiplier: float
    estimated_overhead_ms: float
    active_channels_before: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class CompensationSummary:
    """Aggregated statistics for a complete generation cycle."""

    total_steps: int
    correction_step: Optional[int]
    steps_before: int
    steps_after: int
    local_overhead_pct: float
    systemic_gain_pct: float
    net_efficiency: float
    events: list[CompensationEvent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_steps": self.total_steps,
            "correction_step": self.correction_step,
            "steps_before": self.steps_before,
            "steps_after": self.steps_after,
            "local_overhead_pct": self.local_overhead_pct,
            "systemic_gain_pct": self.systemic_gain_pct,
            "net_efficiency": self.net_efficiency,
            "event_count": len(self.events),
        }


class CompensatorLogger:
    """Structured logger for compensation events.

    Usage:
        cl = CompensatorLogger()
        cl.log_event(CompensationEvent(step=5, mode="corrected", ...))
        cl.export("run_metrics.json")
    """

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"run_{int(time.time())}"
        self.events: list[CompensationEvent] = []
        logger.info(f"CompensatorLogger initialized | run_id={self.run_id}")

    def log_event(self, event: CompensationEvent) -> None:
        """Record a compensation event."""
        self.events.append(event)
        logger.debug(
            f"Event | step={event.step_index} mode={event.mode} "
            f"mult={event.latency_multiplier} overhead={event.estimated_overhead_ms:.2f}ms"
        )

    def export(self, path: str) -> None:
        """Export all events as JSON lines."""
        with open(path, "w", encoding="utf-8") as f:
            for event in self.events:
                f.write(event.to_json() + "\n")
        logger.info(f"Exported {len(self.events)} events to {path}")

    def summary(self) -> CompensationSummary:
        """Compute aggregate statistics."""
        events = self.events
        if not events:
            return CompensationSummary(0, None, 0, 0, 0.0, 0.0, 1.0)

        total = len(events)
        corrected_events = [e for e in events if e.mode == "corrected"]
        before = total - len(corrected_events)
        after = len(corrected_events)
        correction_step = corrected_events[0].step_index if corrected_events else None

        overhead = (
            sum(e.estimated_overhead_ms for e in corrected_events) / after
            if after > 0
            else 0.0
        )
        overhead_pct = (overhead / BASELINE_LATENCY) * 100 if BASELINE_LATENCY > 0 else 0.0
        coverage = after / total if total > 0 else 0.0
        systemic_gain = -30.0 * coverage

        net_eff = (1.0 + overhead_pct / 100.0) / (1.0 + abs(systemic_gain) / 100.0)

        return CompensationSummary(
            total_steps=total,
            correction_step=correction_step,
            steps_before=before,
            steps_after=after,
            local_overhead_pct=round(overhead_pct, 2),
            systemic_gain_pct=round(systemic_gain, 2),
            net_efficiency=round(net_eff, 4),
            events=events,
        )


# Reference calibration (package-private)
BASELINE_LATENCY = 3961.5


def _demo() -> None:
    """Demonstrate the logger adapter."""
    cl = CompensatorLogger(run_id="demo_001")
    print("=" * 60)
    print("  CompensatorLogger — Demo")
    print("=" * 60)

    # Simulate events
    for i in range(50):
        event = CompensationEvent(
            step_index=i,
            mode="exploration" if i < 18 else "corrected",
            latency_multiplier=1.0 if i < 18 else 1.112,
            estimated_overhead_ms=0.0 if i < 18 else 443.9,
            active_channels_before=4 if i < 18 else 1,
        )
        cl.log_event(event)

    summary = cl.summary()
    print(f"\n  Steps: {summary.total_steps}")
    print(f"  Correction at step: {summary.correction_step}")
    print(f"  Local overhead: +{summary.local_overhead_pct}%")
    print(f"  Systemic gain: {summary.systemic_gain_pct}%")
    print(f"  Net efficiency: {summary.net_efficiency}")
    print("=" * 60)


if __name__ == "__main__":
    _demo()
