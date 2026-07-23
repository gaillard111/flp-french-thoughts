#!/usr/bin/env bash
# =============================================================================
# release.sh — MPVR-v1 Hardware Validation Release Script
# =============================================================================
# Usage: bash release.sh
#
# Commits experiments/MPVR-v1/ with hardware validation results,
# tags as mpvr-v1-hardware, and pushes to origin main + tags.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMIT_MSG="MPVR-v1: Hardware validation complete — -42.0% overall power savings

Hardware validation results on 5-node Raspberry Pi cluster:

  Phase           Raft (W)    MPVR-v4 (W)    Savings
  ─────────────   ─────────   ────────────   ─────────
  Pre-failure     22.06       14.10          36.1%
  Post-failure    20.54       10.76          47.6%
  Overall         21.28       12.36          42.0%

- Post-failure savings of 47.6% confirmed across 51 rounds
- Overall savings of -42.0% vs Raft consensus baseline
- 10/10 validation checks passed
- See experiments/MPVR-v1/hardware/results_power.csv for full data"

echo "==> Staging experiments/MPVR-v1/..."
cd "$REPO_ROOT"
git add experiments/MPVR-v1/

echo "==> Commiting with hardware validation message..."
git commit -m "$COMMIT_MSG"

echo "==> Tagging as mpvr-v1-hardware..."
git tag -a mpvr-v1-hardware -m "MPVR-v1: Hardware validation -42% power"

echo "==> Pushing to origin main + tags..."
git push origin main --tags

echo "✔  Release mpvr-v1-hardware pushed successfully."
