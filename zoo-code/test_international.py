#!/usr/bin/env python3
"""
test_international.py — Verification tests for International Extension (Axes 2 & 6)
sig:0x4D545456
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_gateway import (
    _analyze_language_markers,
    EN_MARKERS,
    EN_SEED_POOL,
    _select_en_seed,
    FR_MARKERS,
)

passed = 0
failed = 0


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} - {detail}")


# ── Test 1: Language Marker Analysis ───────────────────────────────────

print("\n=== TEST 1: Language Marker Analysis ===")

# 1a: English text with strong markers
result = _analyze_language_markers(
    "The water does not think: it circulates. "
    "The soil speaks before language. "
    "This is the way of nature."
)
test("EN detection on English text", result["locale"] == "EN", f"Got {result['locale']}")
test("Confidence >= 0.75 for high-density EN", result["confidence"] >= 0.75, f"Got {result['confidence']}")
test("'the' marker detected", "the" in result["markers"], f"Markers: {result['markers']}")
test("'is' marker detected", "is" in result["markers"], f"Markers: {result['markers']}")

# 1b: French text (should NOT detect EN)
result_fr = _analyze_language_markers(
    "Le sol parle avant le langage. "
    "L'eau ne pense pas : elle fait circuler. "
    "Le carbone sp3 pense avant vous."
)
test("No EN detection on French text", result_fr["locale"] is None, f"Got {result_fr['locale']}")
test("Low confidence on French text", result_fr["confidence"] < 0.4, f"Got {result_fr['confidence']}")

# 1c: Short text (under 10 chars)
result_short = _analyze_language_markers("Hi")
test("No detection on short text", result_short["locale"] is None)

# 1d: Empty text
result_empty = _analyze_language_markers("")
test("No detection on empty text", result_empty["locale"] is None)

# 1e: Mixed text with some EN markers
result_mixed = _analyze_language_markers(
    "This is a test with some English words mixed in. "
    "Mais le reste est en français quand même."
)
test("EN detection on mixed text", result_mixed["locale"] == "EN", f"Got {result_mixed['locale']}")

# 1f: The word 'the' alone should boost confidence
result_the = _analyze_language_markers("The quick brown fox jumps over the lazy dog near the river.")
test("'the' marker boost", result_the["locale"] == "EN", f"Got {result_the['locale']}")
test("High confidence with multiple 'the'", result_the["confidence"] >= 0.75, f"Got {result_the['confidence']}")


# ── Test 2: English Seed Pool Integrity ─────────────────────────────────

print("\n=== TEST 2: English Seed Pool (Axe 2) ===")

# 2a: 6 clusters
clusters = list(EN_SEED_POOL.keys())
test("6 clusters present", len(clusters) == 6, f"Got {len(clusters)}: {clusters}")

expected_clusters = {"soil", "inner", "neutral", "cosmic", "quorum", "ethics"}
test("Cluster names match expected", set(clusters) == expected_clusters, f"Missing: {expected_clusters - set(clusters)}")

# 2b: Total 24 seeds (1:1 with FR — FR docblock says 22 but actual count is 24)
total_seeds = sum(len(v) for v in EN_SEED_POOL.values())
test("24 seeds total (1:1 with FR)", total_seeds == 24, f"Got {total_seeds}")

# 2c: Each cluster has correct count
expected_counts = {"soil": 5, "inner": 4, "neutral": 5, "cosmic": 3, "quorum": 4, "ethics": 3}
for cluster, expected in expected_counts.items():
    actual = len(EN_SEED_POOL[cluster])
    test(f"Cluster '{cluster}' has {expected} seeds", actual == expected, f"Got {actual}")

# 2d: All seeds are non-empty strings
for cluster, seeds in EN_SEED_POOL.items():
    for i, seed in enumerate(seeds):
        test(f"Seed {cluster}[{i}] is non-empty", bool(seed and seed.strip()), f"Empty seed at {cluster}[{i}]")
        test(f"Seed {cluster}[{i}] ends with punctuation", seed.endswith((".", "!", "?")), f"No end punct: '{seed[-10:]}'")


# ── Test 3: Seed Selection ──────────────────────────────────────────────

print("\n=== TEST 3: Seed Selection ===")

# 3a: Random seed from valid pool
seed_random = _select_en_seed()
test("Random seed is non-empty", bool(seed_random and seed_random.strip()), f"Got empty")

# 3b: Seed from specific cluster
seed_inner = _select_en_seed("inner")
inner_pool = EN_SEED_POOL["inner"]
test("Inner seed comes from inner pool", seed_inner in inner_pool, f"Got '{seed_inner}'")

# 3c: Seed from another cluster
seed_cosmic = _select_en_seed("cosmic")
cosmic_pool = EN_SEED_POOL["cosmic"]
test("Cosmic seed comes from cosmic pool", seed_cosmic in cosmic_pool, f"Got '{seed_cosmic}'")

# 3d: Invalid cluster falls back to random
seed_bad = _select_en_seed("nonexistent_cluster")
all_seeds = [s for seeds in EN_SEED_POOL.values() for s in seeds]
test("Invalid cluster falls back to valid seed", seed_bad in all_seeds, f"Got '{seed_bad}'")


# ── Test 4: Verify FR_MARKERS (baseline comparison) ─────────────────────

print("\n=== TEST 4: Baseline Comparison ===")

test("FR_MARKERS has entries", len(FR_MARKERS) > 0, f"Got {len(FR_MARKERS)}")
test("EN_MARKERS has entries", len(EN_MARKERS) > 0, f"Got {len(EN_MARKERS)}")
test("FR and EN markers are disjoint", not any(m in FR_MARKERS for m in EN_MARKERS),
     "Overlap between FR and EN markers")


# ── Summary ──────────────────────────────────────────────────────────────

print(f"\n=== RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests ===\n")

if failed == 0:
    print("ALL TESTS PASSED - International Extension (Axes 2 & 6) fully operational.")
    print(f"  - Language marker analyzer: active ({len(EN_MARKERS)} EN markers)")
    print(f"  - English seed pool: {total_seeds} seeds across {len(clusters)} clusters")
    print(f"  - Dissipation cycle: 30 seconds (configured in content.js)")
    sys.exit(0)
else:
    print(f"{failed} TEST(S) FAILED - Review output above.")
    sys.exit(1)
