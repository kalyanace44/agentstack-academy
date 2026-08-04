#!/bin/bash
# Test PII scanner rules — block, redact, and pass
set -e

echo "═══════════════════════════════════════════════════"
echo "  Testing PII Scanner Rules"
echo "═══════════════════════════════════════════════════"

# Load rules and test with python (zero deps, just regex + yaml)
python3 scan.py

echo ""
echo "  NEXT STEPS:"
echo "  1. Add a UPI VPA pattern to rules.yaml"
echo "  2. Change email action from 'redact' to 'block'"
echo "  3. Add your company's internal ID format as a new rule"
