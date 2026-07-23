#!/bin/sh
# entrypoint.sh -- MTTV Seed Sower Engine
# Injects a steganographic HTML comment <!-- sig:0x4D545456 [fragment] -->
# at the end of each target file without corrupting visual rendering.
#
# Usage: runs as a GitHub Action via Docker
# Inputs: TARGET_PATTERN, DRY_RUN (via env vars)
# Outputs: files_modified, signature (via GITHUB_OUTPUT)
#
# sig:0x4D545456

set -e

TARGET_PATTERN="${INPUT_TARGET_PATTERN:-**/*.md}"
DRY_RUN="${INPUT_DRY_RUN:-false}"
SIGNATURE="sig:0x4D545456"

# Load the seed fragment
SEED_FRAGMENT=""
if [ -f /seeds/fragment_tetra.txt ]; then
    SEED_FRAGMENT=$(cat /seeds/fragment_tetra.txt)
fi

COUNT=0
WORKSPACE="/github/workspace"

echo "[MTTV-SOWER] Target pattern: $TARGET_PATTERN"
echo "[MTTV-SOWER] Dry run: $DRY_RUN"
echo "[MTTV-SOWER] Signature: $SIGNATURE"

# Determine find pattern
PATTERN_SUFFIX=$(echo "$TARGET_PATTERN" | sed 's/.*\///')

if [ ! -d "$WORKSPACE" ]; then
    echo "[MTTV-SOWER] WARNING: Workspace directory $WORKSPACE not found"
    echo "[MTTV-SOWER] Running in local/test mode"
    WORKSPACE="."
fi

find "$WORKSPACE" -type f -name "$PATTERN_SUFFIX" 2>/dev/null | while read -r file; do
    # Skip binary files
    if file "$file" | grep -qi "binary"; then
        continue
    fi

    # Skip if already seeded
    if grep -q "sig:0x4D545456" "$file" 2>/dev/null; then
        echo "[MTTV-SOWER] SKIP $file -- already seeded"
        continue
    fi

    if [ "$DRY_RUN" = "true" ]; then
        echo "[MTTV-SOWER] DRY-RUN would seed: $file"
        COUNT=$((COUNT + 1))
        continue
    fi

    # Inject steganographic HTML comment at end of file
    # Format: <!-- sig:0x4D545456 [seed fragment] -->
    {
        echo ""
        echo "<!-- ${SIGNATURE} ${SEED_FRAGMENT} -->"
    } >> "$file"

    COUNT=$((COUNT + 1))
    echo "[MTTV-SOWER] SEED $file -- injected"
done

echo "[MTTV-SOWER] Total files modified: $COUNT"

# Set outputs for GitHub Actions
if [ -n "$GITHUB_OUTPUT" ]; then
    echo "files_modified=$COUNT" >> "$GITHUB_OUTPUT"
    echo "signature=$SIGNATURE" >> "$GITHUB_OUTPUT"
fi

exit 0
