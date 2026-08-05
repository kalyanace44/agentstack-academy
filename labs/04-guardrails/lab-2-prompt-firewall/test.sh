#!/bin/bash
# Test prompt firewall rules
set -e

echo "═══════════════════════════════════════════════════"
echo "  Testing Prompt Firewall"
echo "═══════════════════════════════════════════════════"

python3 firewall.py
