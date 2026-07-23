#!/usr/bin/env bash
# =============================================================================
# create_release.sh — MPVR-v1 GitHub Release via GitHub CLI
# =============================================================================
# Usage: bash create_release.sh
#
# Prerequisites:
#   - GitHub CLI (gh) installed and authenticated:
#       gh auth login
#   - Remote set to gaillard111/MPVR-v1
#
# Creates a GitHub Release tagged mpvr-v1-hardware with:
#   - Title: MPVR-v1: Hardware Validation -42% Power Consumption
#   - Body: key metrics table
#   - Attachments: results_power.csv, dashboard.html
#   - Marked as latest release
# =============================================================================

set -euo pipefail

# ── Pre-flight checks ──────────────────────────────────────────────────────

if ! command -v gh &>/dev/null; then
    echo "✖  GitHub CLI (gh) is not installed."
    echo "   Install it from: https://cli.github.com/"
    exit 1
fi

if ! gh auth status &>/dev/null; then
    echo "✖  GitHub CLI is not authenticated."
    echo "   Run: gh auth login"
    exit 1
fi

# ── Locate repository root ─────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE_TAG="mpvr-v1-hardware"

# ── Verify attachment files exist ──────────────────────────────────────────

CSV="$REPO_ROOT/experiments/MPVR-v1/hardware/results_power.csv"
DASHBOARD="$REPO_ROOT/experiments/MPVR-v1/observability/dashboard.html"

for f in "$CSV" "$DASHBOARD"; do
    if [ ! -f "$f" ]; then
        echo "✖  Missing attachment: $f"
        exit 1
    fi
done

# ── Compose release body ───────────────────────────────────────────────────

RELEASE_BODY=$(cat <<-EOF
## MPVR-v1 Hardware Validation — 5-Node Raspberry Pi Cluster

**10/10 checks passed.** MPVR-v4 consensus achieves significant power savings over standard Raft consensus on physical hardware.

### Power Consumption Results

| Phase | Raft (W) | MPVR-v4 (W) | Savings |
|-------|----------|-------------|---------|
| Pre-failure | 22.06 | 14.10 | 36.1% |
| Post-failure | 20.54 | 10.76 | 47.6% |
| **Overall** | **21.28** | **12.36** | **-42.0%** |

### Key Takeaways

- **-42.0% overall** power vs Raft on identical 5-node cluster
- **-47.6% post-failure** — MPVR-v4 excels under degraded conditions
- Multi-path vector routing eliminates leader-election overhead
- Quorum-poreux mechanism reduces idle chatter after node failure

### Attachments

- \`results_power.csv\` — Full 100-round power measurement dataset
- \`dashboard.html\` — Self-contained observability dashboard

### Reproduce

\`\`\`bash
cd hardware
python3 measure_power.py --nodes 5 --rounds 100
\`\`\`
EOF
)

# ── Create GitHub release ──────────────────────────────────────────────────

echo "==> Creating GitHub release $RELEASE_TAG ..."

gh release create "$RELEASE_TAG" \
    --title "MPVR-v1: Hardware Validation -42% Power Consumption" \
    --notes "$RELEASE_BODY" \
    --latest \
    "$CSV" \
    "$DASHBOARD"

echo "✔  Release $RELEASE_TAG created successfully on GitHub."
echo "   View at: https://github.com/gaillard111/MPVR-v1/releases/tag/$RELEASE_TAG"
