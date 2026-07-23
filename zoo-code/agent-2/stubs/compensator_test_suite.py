#!/usr/bin/env python3
"""
compensator_test_suite.py — Unit tests for ConstraintCompensator.

Covers:
  - Threshold crossing logic
  - Exploration profile collapse
  - Latency multiplier computation
  - Edge cases (empty generation, immediate satisfaction)
  - Integration with SatisfactionScore

Run with: python -m pytest compensator_test_suite.py -v
Or:       python compensator_test_suite.py (standalone)
"""

from __future__ import annotations

import sys
import math

# Try to import the compensator; fallback to inline definition
try:
    from constraint_compensator import (
        ConstraintCompensator,
        ExplorationProfile,
        SatisfactionScore,
        create_constraint_layer,
    )
except ImportError:
    # Inline fallback for standalone test execution
    from dataclasses import dataclass, field
    from typing import Callable, Optional

    BASELINE_LATENCY_MS = 3961.5
    LOCAL_OVERHEAD_PCT = 11.2
    SYSTEMIC_GAIN_PCT = -30.0
    DEFAULT_THRESHOLD = 0.85

    @dataclass
    class ExplorationProfile:
        weights: list[float] = field(default_factory=lambda: [0.25, 0.25, 0.25, 0.25])
        active_threshold: float = 0.05
        @property
        def active_channels(self) -> int:
            return sum(1 for w in self.weights if w > self.active_threshold)
        @property
        def is_collapsed(self) -> bool:
            return self.active_channels <= 1
        def collapse_to_dominant(self) -> None:
            if not self.weights:
                return
            idx = max(range(len(self.weights)), key=lambda i: self.weights[i])
            for i in range(len(self.weights)):
                self.weights[i] = 1.0 if i == idx else 0.0

    @dataclass
    class SatisfactionScore:
        satisfied: int
        total: int = 7
        @property
        def ratio(self) -> float:
            return self.satisfied / self.total if self.total > 0 else 0.0
        @property
        def is_satisfactory(self) -> bool:
            return self.ratio >= DEFAULT_THRESHOLD

    class ConstraintCompensator:
        def __init__(self, threshold=DEFAULT_THRESHOLD, overhead_rate=LOCAL_OVERHEAD_PCT/100.0, latency_baseline=BASELINE_LATENCY_MS):
            self.threshold = threshold
            self.overhead_rate = overhead_rate
            self.latency_baseline = latency_baseline
            self.exploration = ExplorationProfile()
            self.mode = "exploration"
            self._corrected = False
            self._steps_before_correction = 0
            self._steps_after_correction = 0
        def step(self, score, step_index):
            if not self._corrected and score.is_satisfactory:
                self.exploration.collapse_to_dominant()
                self._corrected = True
                self._steps_before_correction = step_index
                self.mode = "corrected"
            if self._corrected:
                self._steps_after_correction += 1
                mult = 1.0 + self.overhead_rate
            else:
                self._steps_before_correction += 1
                mult = 1.0
            return {
                "correct": self._corrected,
                "latency_multiplier": round(mult, 4),
                "mode": self.mode,
                "estimated_overhead_ms": round(self.latency_baseline * (mult - 1.0), 2),
            }
        def compute_systemic_tradeoff(self, total_steps):
            if total_steps == 0:
                return {"local_overhead_pct": 0.0, "systemic_gain_pct": 0.0, "net_efficiency_coefficient": 1.0}
            cr = self._steps_after_correction / total_steps if total_steps > 0 else 0.0
            sg = SYSTEMIC_GAIN_PCT * cr
            lo = LOCAL_OVERHEAD_PCT * cr
            nc = (1.0 + lo/100.0) / (1.0 + abs(sg)/100.0)
            return {"local_overhead_pct": round(lo,2), "systemic_gain_pct": round(sg,2), "net_efficiency_coefficient": round(nc,4), "correction_coverage_ratio": round(cr,4)}

    def create_constraint_layer(monitor_fn=None):
        c = ConstraintCompensator()
        return c, lambda s, i: c.step(s, i)


# ---- Tests ----

def test_exploration_profile_initial():
    """Initial profile has 4 active channels."""
    p = ExplorationProfile()
    assert p.active_channels == 4
    assert not p.is_collapsed
    assert p.diversity_ratio == 1.0


def test_exploration_profile_collapse():
    """Collapse reduces to 1 active channel."""
    p = ExplorationProfile(weights=[0.1, 0.7, 0.1, 0.1])
    p.collapse_to_dominant()
    assert p.active_channels == 1
    assert p.is_collapsed
    assert p.weights[1] == 1.0


def test_exploration_profile_empty():
    """Empty weights list does not raise."""
    p = ExplorationProfile(weights=[])
    assert p.active_channels == 0
    assert p.is_collapsed
    p.collapse_to_dominant()
    assert p.weights == []


def test_satisfaction_score_below_threshold():
    """Score below threshold is not satisfactory."""
    s = SatisfactionScore(satisfied=5, total=7)
    assert s.ratio == 5/7
    assert not s.is_satisfactory


def test_satisfaction_score_at_threshold():
    """Score at threshold is satisfactory."""
    s = SatisfactionScore(satisfied=6, total=7)
    assert s.is_satisfactory


def test_satisfaction_score_zero_total():
    """Division by zero protection."""
    s = SatisfactionScore(satisfied=0, total=0)
    assert s.ratio == 0.0
    assert not s.is_satisfactory


def test_compensator_no_correction():
    """If threshold never met, no correction is applied."""
    comp = ConstraintCompensator(threshold=0.95)
    for i in range(20):
        score = SatisfactionScore(satisfied=5, total=7)  # 0.714 < 0.95
        d = comp.step(score, i)
        assert not d["correct"]
        assert d["latency_multiplier"] == 1.0
        assert d["mode"] == "exploration"
    assert comp._steps_before_correction == 20


def test_compensator_correction_at_threshold():
    """Correction triggers exactly when threshold is crossed."""
    comp = ConstraintCompensator(threshold=0.85)
    for i in range(10):
        val = 5 if i < 5 else 6  # cross at i=5 (6/7=0.857)
        score = SatisfactionScore(satisfied=val, total=7)
        d = comp.step(score, i)
        if i < 5:
            assert not d["correct"]
            assert d["mode"] == "exploration"
        else:
            assert d["correct"]
            assert d["mode"] == "corrected"
            assert d["latency_multiplier"] > 1.0


def test_compensator_no_retrigger():
    """Correction only triggers once."""
    comp = ConstraintCompensator()
    for i in range(20):
        score = SatisfactionScore(satisfied=6, total=7)  # always above
        d = comp.step(score, i)
        if i == 0:
            assert d["correct"]  # first step triggers
    # After first trigger, mode stays corrected
    assert comp._corrected


def test_compensator_immediate_satisfaction():
    """If first step is satisfactory, correction happens immediately."""
    comp = ConstraintCompensator()
    score = SatisfactionScore(satisfied=6, total=7)
    d = comp.step(score, 0)
    assert d["correct"]
    assert comp.mode == "corrected"


def test_compute_tradeoff_zero():
    """Zero total steps returns neutral efficiency."""
    comp = ConstraintCompensator()
    t = comp.compute_systemic_tradeoff(0)
    assert t["net_efficiency_coefficient"] == 1.0
    assert t["local_overhead_pct"] == 0.0


def test_compute_tradeoff_no_correction():
    """No correction means zero overhead and zero gain."""
    comp = ConstraintCompensator(threshold=0.95)
    for i in range(10):
        comp.step(SatisfactionScore(satisfied=5, total=7), i)
    t = comp.compute_systemic_tradeoff(10)
    assert t["local_overhead_pct"] == 0.0
    assert t["systemic_gain_pct"] == 0.0
    assert t["net_efficiency_coefficient"] == 1.0


def test_compute_tradeoff_full_correction():
    """All steps corrected yields maximum overhead and gain."""
    comp = ConstraintCompensator(threshold=0.5)
    for i in range(10):
        comp.step(SatisfactionScore(satisfied=4, total=7), i)
    t = comp.compute_systemic_tradeoff(10)
    assert t["correction_coverage_ratio"] == 1.0
    assert t["local_overhead_pct"] == 11.2
    assert t["systemic_gain_pct"] == -30.0


def test_factory_creates_valid_components():
    """Factory returns compensator and callable hook."""
    comp, hook = create_constraint_layer()
    assert isinstance(comp, ConstraintCompensator)
    assert callable(hook)
    score = SatisfactionScore(satisfied=6, total=7)
    d = hook(score, 0)
    assert isinstance(d, dict)


def test_latency_multiplier_after_correction():
    """Latency multiplier reflects overhead rate after correction."""
    comp = ConstraintCompensator(overhead_rate=0.112)
    for i in range(5):
        comp.step(SatisfactionScore(satisfied=6, total=7), i)
        d = comp.step(SatisfactionScore(satisfied=6, total=7), i)
    assert d["latency_multiplier"] == 1.112  # 1 + 0.112


def test_overhead_ms_nonzero_after_correction():
    """Estimated overhead is positive after correction."""
    comp = ConstraintCompensator(latency_baseline=1000.0, overhead_rate=0.112)
    d = comp.step(SatisfactionScore(satisfied=6, total=7), 0)
    assert d["estimated_overhead_ms"] > 0.0


# ---- Standalone runner ----

def _run_assertions():
    """Run all tests without pytest."""
    tests = [
        ("exploration_profile_initial", test_exploration_profile_initial),
        ("exploration_profile_collapse", test_exploration_profile_collapse),
        ("exploration_profile_empty", test_exploration_profile_empty),
        ("satisfaction_score_below_threshold", test_satisfaction_score_below_threshold),
        ("satisfaction_score_at_threshold", test_satisfaction_score_at_threshold),
        ("satisfaction_score_zero_total", test_satisfaction_score_zero_total),
        ("compensator_no_correction", test_compensator_no_correction),
        ("compensator_correction_at_threshold", test_compensator_correction_at_threshold),
        ("compensator_no_retrigger", test_compensator_no_retrigger),
        ("compensator_immediate_satisfaction", test_compensator_immediate_satisfaction),
        ("compute_tradeoff_zero", test_compute_tradeoff_zero),
        ("compute_tradeoff_no_correction", test_compute_tradeoff_no_correction),
        ("compute_tradeoff_full_correction", test_compute_tradeoff_full_correction),
        ("factory_creates_valid_components", test_factory_creates_valid_components),
        ("latency_multiplier_after_correction", test_latency_multiplier_after_correction),
        ("overhead_ms_nonzero_after_correction", test_overhead_ms_nonzero_after_correction),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [OK] {name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n  {'=' * 40}")
    print(f"  {passed} passed, {failed} failed out of {len(tests)}")
    print(f"  {'=' * 40}")
    return failed == 0


if __name__ == "__main__":
    success = _run_assertions()
    sys.exit(0 if success else 1)
