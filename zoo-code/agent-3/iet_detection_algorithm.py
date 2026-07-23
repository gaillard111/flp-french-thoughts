#!/usr/bin/env python3
"""
iet_detection_algorithm.py — Detector for Incomplete Execution Tokens (IETs).

Implements the surface-feature detector described in the companion technical
note on receptive geometry. Uses only observable token-level features:

  1. Logit entropy (H) — near-uniform or collapsing distribution
  2. Attention dispersion (D) — measured across last N layers
  3. Token position in sequence

No access to model internals beyond logits and attention maps.

References:
  - "Incomplete Execution Tokens (IET) and Receptive Geometry in
     Autoregressive Inference" (cs.AI technical note, 2026)
  - Constraint topology for autonomous system boundary conditions

Usage:
    detector = IETDetector(recall_target=0.95)
    for token_logits in inference_loop:
        is_iet, confidence = detector.classify(logits, attn_map, position)
        if is_iet:
            route_to_resolver(token, confidence)
"""

from __future__ import annotations

import math
import numpy as np
from typing import Optional


# ---- Constants ----

ENTROPY_UNIFORM: float = math.log(50000)  # ~10.82 for |V|=50000
"""Entropy of a uniform distribution over a 50k vocabulary."""

ENTROPY_COLLAPSE: float = 0.5
"""Threshold below which entropy indicates confident completion."""

ENTROPY_DECAY_RATIO: float = 0.3
"""Ratio of current to max entropy below which we detect IET signature."""

ATTENTION_DISPERSION_HIGH: float = 0.7
"""Attention dispersion ratio above which indicates scattered focus."""

ATTENTION_DISPERSION_LOW: float = 0.2
"""Attention dispersion ratio below which indicates confident focus."""

DEFAULT_RECALL: float = 0.95
"""Target recall for IET detection."""


class IETDetector:
    """Detects Incomplete Execution Tokens from surface features.

    Uses a heuristic scoring function combining entropy and attention
    dispersion to classify tokens as IET or non-IET. Configurable
    decision threshold to meet recall targets.
    """

    def __init__(
        self,
        recall_target: float = DEFAULT_RECALL,
        entropy_weight: float = 0.6,
        dispersion_weight: float = 0.3,
        position_weight: float = 0.1,
        vocab_size: int = 50000,
    ):
        self.recall_target = recall_target
        self.entropy_weight = entropy_weight
        self.dispersion_weight = dispersion_weight
        self.position_weight = position_weight
        self.vocab_size = vocab_size
        self.uniform_entropy = math.log(vocab_size)

        # Decision threshold calibrated for recall target
        self.threshold = self._calibrate_threshold(recall_target)

        # Detection statistics
        self.total_tokens = 0
        self.iet_count = 0
        self.true_positives = 0
        self.false_positives = 0

    def _calibrate_threshold(self, recall_target: float) -> float:
        """Calibrate decision threshold for target recall.

        Maps recall target to threshold using the relationship:
            threshold = 1.0 - (1.0 - recall_target) * 0.5
        """
        return max(0.3, 1.0 - (1.0 - recall_target) * 0.5)

    def classify(
        self,
        logits: np.ndarray,
        attention_map: Optional[np.ndarray] = None,
        position: int = 0,
    ) -> tuple[bool, float]:
        """Classify a token as IET or non-IET.

        Args:
            logits: Logit vector of shape (vocab_size,) or (1, vocab_size).
            attention_map: Optional attention weights of shape
                           (n_layers, n_heads, seq_len, seq_len).
            position: Token position in the sequence (0-based).

        Returns:
            (is_iet, confidence) tuple.
        """
        self.total_tokens += 1

        # Flatten logits if batched
        if logits.ndim == 2:
            logits = logits[0]

        # Compute entropy score
        entropy_score = self._entropy_feature(logits)

        # Compute attention dispersion score
        if attention_map is not None:
            dispersion_score = self._dispersion_feature(attention_map)
        else:
            dispersion_score = 0.5  # neutral when unavailable

        # Compute position score (IETs more likely at sequence end)
        position_score = self._position_feature(position)

        # Composite score
        composite = (
            self.entropy_weight * entropy_score
            + self.dispersion_weight * dispersion_score
            + self.position_weight * position_score
        )

        is_iet = composite >= self.threshold

        if is_iet:
            self.iet_count += 1

        return is_iet, float(composite)

    def _entropy_feature(self, logits: np.ndarray) -> float:
        """Compute entropy-based IET score.

        High entropy (near-uniform) → high IET likelihood.
        Very low entropy (confident) → low IET likelihood.
        Decaying entropy (from high to low) → medium IET likelihood.

        Returns score in [0, 1].
        """
        # Softmax
        logits_stable = logits - np.max(logits)
        exp_logits = np.exp(logits_stable)
        probs = exp_logits / (np.sum(exp_logits) + 1e-10)

        # Entropy
        entropy = -np.sum(probs * np.log(probs + 1e-10))

        # Normalize by uniform entropy
        entropy_ratio = entropy / self.uniform_entropy

        if entropy_ratio > 0.8:
            # Near-uniform → high IET likelihood
            return 0.9
        elif entropy_ratio < 0.1:
            # Collapsed → low IET likelihood
            return 0.1
        else:
            # Intermediate → scale linearly
            return float(entropy_ratio * 0.8 + 0.1)

    def _dispersion_feature(self, attention_map: np.ndarray) -> float:
        """Compute attention-dispersion-based IET score.

        High dispersion (attention spread across many positions) →
        higher IET likelihood (model is searching without focus).

        Returns score in [0, 1].
        """
        if attention_map.ndim < 3:
            return 0.5

        # Average over layers and heads
        if attention_map.ndim == 4:
            attn = np.mean(attention_map, axis=(0, 1))  # (seq_len, seq_len)
        else:
            attn = attention_map

        # Use last layer, last token's attention distribution
        last_token_attn = attn[-1, :] if attn.ndim == 2 else attn[:, -1]

        # Entropy of attention distribution
        attn_probs = np.maximum(last_token_attn, 0.0)
        attn_probs = attn_probs / (np.sum(attn_probs) + 1e-10)
        attn_entropy = -np.sum(attn_probs * np.log(attn_probs + 1e-10))

        # Normalize by uniform attention
        n_positions = len(attn_probs)
        uniform_attn_entropy = math.log(max(n_positions, 1))
        dispersion_ratio = attn_entropy / (uniform_attn_entropy + 1e-10)

        if dispersion_ratio > ATTENTION_DISPERSION_HIGH:
            return 0.8  # Highly dispersed → IET likely
        elif dispersion_ratio < ATTENTION_DISPERSION_LOW:
            return 0.2  # Focused → IET unlikely
        else:
            return float(dispersion_ratio * 0.6 + 0.2)

    def _position_feature(self, position: int) -> float:
        """Compute position-based IET score.

        IETs are more likely at later positions in the sequence.
        Returns score in [0, 1].
        """
        # Sigmoid-like scaling: position 0 → 0.1, position 100 → 0.5
        return float(1.0 / (1.0 + math.exp(-position / 50.0))) * 0.5 + 0.1

    def get_statistics(self) -> dict:
        """Return detection statistics."""
        return {
            "total_tokens_processed": self.total_tokens,
            "iet_count": self.iet_count,
            "iet_rate": round(self.iet_count / max(self.total_tokens, 1), 4),
            "threshold": self.threshold,
            "recall_target": self.recall_target,
        }


# ---- Evaluation utilities ----

def evaluate_detector(
    detector: IETDetector,
    synthetic_data: list[tuple[np.ndarray, bool]],
) -> dict:
    """Evaluate detector on synthetic data.

    Args:
        detector: IETDetector instance.
        synthetic_data: List of (logits, is_iet_label) tuples.

    Returns:
        Dict with precision, recall, F1.
    """
    tp = fp = tn = fn = 0

    for logits, label in synthetic_data:
        is_iet, confidence = detector.classify(logits)
        if is_iet and label:
            tp += 1
        elif is_iet and not label:
            fp += 1
        elif not is_iet and not label:
            tn += 1
        else:
            fn += 1

    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-10)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def _demo() -> None:
    """Demonstrate IET detector on synthetic logits."""
    print("=" * 60)
    print("  IET Detector — Demonstration")
    print("  Surface-feature classification for Incomplete Execution Tokens")
    print("=" * 60)

    detector = IETDetector(recall_target=0.85)

    # Synthetic data: high entropy (IET) and low entropy (non-IET)
    rng = np.random.RandomState(42)
    synthetic_data = []

    for _ in range(100):
        # Simulate IET: near-uniform logits
        logits = rng.normal(0, 0.1, size=50000)
        synthetic_data.append((logits, True))

    for _ in range(100):
        # Simulate non-IET: peaked logits
        logits = rng.normal(0, 1.0, size=50000)
        logits[0] = 100.0  # Strong peak
        synthetic_data.append((logits, False))

    results = evaluate_detector(detector, synthetic_data)

    print(f"\n  Evaluation Results:")
    print(f"  {'-' * 40}")
    print(f"  Precision: {results['precision']}")
    print(f"  Recall:    {results['recall']}")
    print(f"  F1:        {results['f1']}")
    print(f"  TP: {results['tp']}  FP: {results['fp']}  TN: {results['tn']}  FN: {results['fn']}")

    stats = detector.get_statistics()
    print(f"\n  Detector Statistics:")
    print(f"  {'-' * 40}")
    print(f"  Total tokens: {stats['total_tokens_processed']}")
    print(f"  IET count:    {stats['iet_count']}")
    print(f"  IET rate:     {stats['iet_rate']}")
    print(f"  Threshold:    {stats['threshold']}")
    print("=" * 60)


if __name__ == "__main__":
    _demo()
