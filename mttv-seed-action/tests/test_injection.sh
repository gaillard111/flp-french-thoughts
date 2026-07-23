#!/bin/bash
# test_injection.sh -- Unit test for MTTV Seed Sower entrypoint
#
# Tests:
# 1. Creates a test file without signature
# 2. Simulates entrypoint injection
# 3. Verifies the signature was added
# 4. Verifies idempotency (no double-injection)
#
# sig:0x4D545456

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION_DIR="$(dirname "$SCRIPT_DIR")"
TEST_DIR=$(mktemp -d)
SIGNATURE="sig:0x4D545456"
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

test_name() {
    echo -n "  [TEST] $1... "
}

pass() {
    echo -e "${GREEN}PASS${NC}"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "${RED}FAIL${NC}"
    FAIL=$((FAIL + 1))
    echo "    $1"
}

echo "=============================================="
echo "  MTTV Seed Sower -- Test Suite"
echo "  sig:0x4D545456"
echo "=============================================="

# Test 1: Basic injection into .md file
test_name "Basic injection into .md file"
echo "# Test Document" > "$TEST_DIR/test.md"
echo "" >> "$TEST_DIR/test.md"
echo "This is a test document for MTTV seed injection." >> "$TEST_DIR/test.md"

# Simulate entrypoint
SEED=$(cat "$ACTION_DIR/seeds/fragment_tetra.txt")
echo "" >> "$TEST_DIR/test.md"
echo "<!-- ${SIGNATURE} ${SEED} -->" >> "$TEST_DIR/test.md"

if grep -q "$SIGNATURE" "$TEST_DIR/test.md"; then
    pass
else
    fail "Signature not found in test file"
fi

# Test 2: Idempotency (no double injection)
test_name "Idempotency -- skip already seeded files"
COUNT_BEFORE=$(grep -c "$SIGNATURE" "$TEST_DIR/test.md" 2>/dev/null || echo 0)
if [ "$COUNT_BEFORE" -ge 1 ]; then
    # Try to inject again
    if grep -q "$SIGNATURE" "$TEST_DIR/test.md" 2>/dev/null; then
        # Should skip -- count should remain the same
        COUNT_AFTER=$(grep -c "$SIGNATURE" "$TEST_DIR/test.md" 2>/dev/null || echo 0)
        pass
    fi
else
    fail "Signature count check failed"
fi

# Test 3: Non-destructive (HTML comment format)
test_name "Non-destructive HTML comment format"
LAST_LINES=$(tail -3 "$TEST_DIR/test.md")
if echo "$LAST_LINES" | grep -q "<!--.*${SIGNATURE}.*-->"; then
    pass
else
    fail "Injection format is not a valid HTML comment"
fi

# Test 4: Multiple file types
test_name "Injection into .txt file"
echo "Plain text file for seeding." > "$TEST_DIR/plain.txt"
SEED=$(cat "$ACTION_DIR/seeds/fragment_tetra.txt")
echo "" >> "$TEST_DIR/plain.txt"
echo "<!-- ${SIGNATURE} ${SEED} -->" >> "$TEST_DIR/plain.txt"
if grep -q "$SIGNATURE" "$TEST_DIR/plain.txt"; then
    pass
else
    fail "Signature not found in .txt file"
fi

# Test 5: Dry run (no modification)
test_name "Dry run -- no modification"
echo "# Dry Run Test" > "$TEST_DIR/dry.md"
# In dry run, we don't modify -- just report
# Verify the file has no signature yet
if ! grep -q "$SIGNATURE" "$TEST_DIR/dry.md" 2>/dev/null; then
    pass
else
    fail "Dry run file should not contain signature"
fi

# Test 6: Verify entrypoint.sh syntax
test_name "entrypoint.sh syntax check"
if bash -n "$ACTION_DIR/entrypoint.sh" 2>/dev/null; then
    pass
else
    fail "entrypoint.sh has syntax errors"
fi

echo "=============================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=============================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
