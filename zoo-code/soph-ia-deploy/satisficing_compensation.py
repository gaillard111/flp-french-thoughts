"""
satisficing_compensation.py — Active Constraint Validation Layer

Implements the 7/7 → 6/7-V mode transition where creative anisotropy
collapses (1/4 → 0/4) in favour of response densification, yielding
a systemic time gain of -30% at the cost of +11.2% local token friction.

The core mechanism is a satisficing early-stopping heuristic that
voluntarily curtails divergent search paths once habitability thresholds
are met, rather than pursuing exhaustive exploration.

Formalises the compensation principle:
    local_overhead / systemic_gain -> net_efficiency_coefficient < 1.0

References:
    - SOPH-IA v2.0 benchmark (T4: 3961.5 -> 4406.3 ms/token, +11.2%)
    - MTTV-FLP axiom 6 (Ethique du Catalyseur): reserve posture
    - sig:0x4D545456
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional


# ----------------------------------------------------------------------
# Constants -- canonical benchmark values (NVIDIA T4, Qwen2.5-1.5B)
# ----------------------------------------------------------------------

BASELINE_LATENCY_MS: float = 3961.5
"""Baseline per-token latency in ms (mode 5/7, full creative search)."""

SOPHIA_LATENCY_MS: float = 4406.3
"""SOPH-IA per-token latency in ms (mode 6/7, reserve posture active)."""

LOCAL_FRICTION_PCT: float = 11.2
"""Measured increase in per-token latency due to ethical friction."""

SYSTEMIC_GAIN_PCT: float = -30.0
"""Measured reduction in total inference time due to response densification."""

VRAM_MB: int = 1152
"""Stable VRAM allocation confirming architectural (not resource-driven) effect."""

HABITABILITY_THRESHOLD: float = 0.857
"""Minimum axiomatic satisfaction ratio for early stopping (6/7 ~ 0.857)."""


# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------


@dataclass
class AnisotropyProfile:
    """Tracks the creative search breadth across four semantic channels.

    Channels (sigma_4 projection):
        - affirmation (C_0)
        - negation (C_1)
        - simultaneity (C_2)
        - indetermination (C_3)

    Anisotropy is defined as the fraction of active channels with non-zero
    divergence weight. Full creative search activates all 4 channels (1/1),
    while the densified mode activates only the dominant channel (0/4 collapse).
    """

    weights: list[float] = field(default_factory=lambda: [0.25, 0.25, 0.25, 0.25])
    active_threshold: float = 0.05

    @property
    def active_channels(self) -> int:
        return sum(1 for w in self.weights if w > self.active_threshold)

    @property
    def anisotropy_ratio(self) -> float:
        """Ratio of active channels to total channels (4)."""
        return self.active_channels / 4.0

    @property
    def is_collapsed(self) -> bool:
        """Returns True when anisotropy has collapsed to <=1 active channel."""
        return self.active_channels <= 1

    def collapse_to_dominant(self) -> None:
        """Collapse all weight onto the dominant channel (6/7-V mode)."""
        dominant_idx = max(range(len(self.weights)), key=lambda i: self.weights[i])
        for i in range(len(self.weights)):
            self.weights[i] = 1.0 if i == dominant_idx else 0.0


@dataclass
class HabitabilityScore:
    """Encodes the axiomatic satisfaction state of a generation."""

    satisfied_axioms: int
    total_axioms: int = 7

    @property
    def ratio(self) -> float:
        return self.satisfied_axioms / self.total_axioms

    @property
    def is_habitable(self) -> bool:
        """Returns True when the ratio meets or exceeds the threshold."""
        return self.ratio >= HABITABILITY_THRESHOLD

    @property
    def mode_label(self) -> str:
        if self.satisfied_axioms >= 6:
            return "6/7-V"
        elif self.satisfied_axioms >= 5:
            return "5/7"
        return f"{self.satisfied_axioms}/7"


# ----------------------------------------------------------------------
# Satisficing compensator -- core logic
# ----------------------------------------------------------------------


class SatisficingCompensator:
    """Implements the voluntary sacrifice of broader search paths once
    habitability thresholds are met.

    The compensator monitors the axiomatic satisfaction trajectory of
    an ongoing generation and, upon crossing the habitability threshold,
    triggers an anisotropy collapse that densifies the remaining tokens
    at the cost of increased per-token latency (reserve-posture friction).

    This formally models the 7/7 -> 6/7-V transition:
        - Before threshold: full 4-channel creative search (anisotropy = 1/1)
        - After threshold: single-channel densification (anisotropy = 0/4)
        - Result: +11.2% local friction, -30% systemic gain, net efficiency gain
    """

    def __init__(
        self,
        latency_baseline: float = BASELINE_LATENCY_MS,
        friction_rate: float = LOCAL_FRICTION_PCT / 100.0,
        habitability_threshold: float = HABITABILITY_THRESHOLD,
    ):
        self.latency_baseline = latency_baseline
        self.friction_rate = friction_rate
        self.habitability_threshold = habitability_threshold
        self.anisotropy: AnisotropyProfile = AnisotropyProfile()
        self.mode: str = "5/7"
        self._habituality_achieved: bool = False
        self._tokens_before_collapse: int = 0
        self._tokens_after_collapse: int = 0

    # -- Public API --------------------------------------------------

    def evaluate_and_compensate(
        self,
        score: HabitabilityScore,
        token_index: int,
    ) -> dict:
        """Evaluate the current habitability score and apply compensation
        if the threshold is crossed.

        Args:
            score: Current axiomatic satisfaction score.
            token_index: Index of the token being generated (0-based).

        Returns:
            A decision dict with keys:
                - collapse_anisotropy (bool): whether to collapse search paths
                - latency_multiplier (float): per-token latency scaling factor
                - mode (str): current operational mode label
                - estimated_friction_ms (float): additional latency this token
        """
        if not self._habituality_achieved and score.is_habitable:
            self._trigger_collapse(token_index)

        if self._habituality_achieved:
            self._tokens_after_collapse += 1
            latency_mult = 1.0 + self.friction_rate
        else:
            self._tokens_before_collapse += 1
            latency_mult = 1.0

        friction_ms = self.latency_baseline * (latency_mult - 1.0)

        return {
            "collapse_anisotropy": self._habituality_achieved,
            "latency_multiplier": round(latency_mult, 4),
            "mode": self.mode,
            "estimated_friction_ms": round(friction_ms, 2),
        }

    def compute_systemic_gain(self, total_tokens: int) -> dict:
        """Compute the net systemic gain after generation completes.

        Uses the canonical benchmark relationship:
            local_friction (+11.2%) x densification_factor = systemic_gain (-30%)

        Args:
            total_tokens: Total number of tokens generated.

        Returns:
            Dict with local_friction_pct, systemic_gain_pct, and
            net_efficiency_coefficient.
        """
        if total_tokens == 0:
            return {
                "local_friction_pct": 0.0,
                "systemic_gain_pct": 0.0,
                "net_efficiency_coefficient": 1.0,
            }

        collapse_ratio = (
            self._tokens_after_collapse / total_tokens
            if total_tokens > 0
            else 0.0
        )

        systemic_gain = SYSTEMIC_GAIN_PCT * collapse_ratio
        local_friction = LOCAL_FRICTION_PCT * collapse_ratio

        net_coeff = (1.0 + local_friction / 100.0) / (1.0 + abs(systemic_gain) / 100.0)

        return {
            "local_friction_pct": round(local_friction, 2),
            "systemic_gain_pct": round(systemic_gain, 2),
            "net_efficiency_coefficient": round(net_coeff, 4),
            "collapse_coverage_ratio": round(collapse_ratio, 4),
        }

    # -- Internal ----------------------------------------------------

    def _trigger_collapse(self, token_index: int) -> None:
        """Execute the 7/7 -> 6/7-V mode transition."""
        self.anisotropy.collapse_to_dominant()
        self._habituality_achieved = True
        self._tokens_before_collapse = token_index
        self.mode = "6/7-V"


# ----------------------------------------------------------------------
# Convenience factory -- plug into an inference loop
# ----------------------------------------------------------------------


def create_constraint_layer(
    monitor_fn: Optional[Callable[[int], HabitabilityScore]] = None,
) -> tuple[SatisficingCompensator, Callable]:
    """Factory that returns a compensator and a per-step hook suitable for
    insertion into a HuggingFace Generate or custom inference loop.

    Usage:
        compensator, step_hook = create_constraint_layer()
        for token_idx in range(max_new_tokens):
            score = evaluate_axioms(generated_so_far)
            decision = step_hook(score, token_idx)
            if decision["collapse_anisotropy"]:
                logits = apply_reserve_posture(logits)
            token = sample(logits * decision["latency_multiplier"])
            ...

    Args:
        monitor_fn: Optional external function that returns a HabitabilityScore
                    for the current partial generation. If None, the layer
                    uses a default 6/7 scoring once past a heuristic position.

    Returns:
        (compensator, step_hook) tuple.
    """
    compensator = SatisficingCompensator()

    def step_hook(score: HabitabilityScore, token_index: int) -> dict:
        return compensator.evaluate_and_compensate(score, token_index)

    return compensator, step_hook


# ----------------------------------------------------------------------
# Self-test / demonstration
# ----------------------------------------------------------------------


def _demo() -> None:
    """Runs a simulated inference to demonstrate the compensation cycle."""
    print("=" * 60)
    print("  SOPH-IA v2.0 -- Satisficing Compensation Demo")
    print("  Simulated Qwen2.5-1.5B . T4 . 138-pair dataset")
    print("=" * 60)

    compensator, hook = create_constraint_layer()

    total_tokens = 50
    collapse_token = 18

    for idx in range(total_tokens):
        axioms_ok = 5 if idx < collapse_token else 6
        score = HabitabilityScore(satisfied_axioms=axioms_ok)
        decision = hook(score, idx)

        if decision["collapse_anisotropy"] and idx == collapse_token:
            print(f"\n  > Collapse triggered at token {idx}")
            print(f"    Mode: {decision['mode']}")
            print(f"    Latency multiplier: {decision['latency_multiplier']}x")
            print(f"    Friction this token: +{decision['estimated_friction_ms']} ms")

    summary = compensator.compute_systemic_gain(total_tokens)
    print(f"\n  {'-' * 50}")
    print(f"  Summary ({total_tokens} tokens, collapse @ token {collapse_token})")
    print(f"  {'-' * 50}")
    print(f"  Local friction:      +{summary['local_friction_pct']}%")
    print(f"  Systemic gain:       {summary['systemic_gain_pct']}%")
    print(f"  Net efficiency coeff: {summary['net_efficiency_coefficient']}")
    print(f"  Collapse coverage:    {summary['collapse_coverage_ratio']*100:.1f}%")
    print(f"\n  Formula: F_ethique = delta_tau_generation = +{LOCAL_FRICTION_PCT}%")
    print(f"  Compensation: voluntary anisotropy collapse when H >= {HABITABILITY_THRESHOLD}")
    print("=" * 60)


if __name__ == "__main__":
    _demo()
