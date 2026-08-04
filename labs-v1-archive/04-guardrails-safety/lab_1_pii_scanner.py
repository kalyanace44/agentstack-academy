"""Lab 4.1: PII Scanner — Detect & Redact Sensitive Data

Build a production PII scanner that:
1. Detects Indian financial identifiers (PAN, Aadhaar, UPI)
2. Detects global PII (email, phone, credit cards, API keys)
3. Redacts or blocks requests before they reach LLM providers
4. Runs in <1ms per request (production-grade)

This is a real production pattern used by fintechs under RBI regulation.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum


# --- Configuration ---

class Action(Enum):
    ALLOW = "allow"      # No PII found, proceed
    REDACT = "redact"    # PII found, redact and forward
    BLOCK = "block"      # Critical PII found, reject entirely


@dataclass
class Finding:
    """A single PII finding."""
    category: str        # email, pan, aadhaar, credit_card, etc.
    matched: str         # The actual matched text
    position: tuple[int, int]  # Start, end position in text
    action: Action       # What to do about it
    severity: str        # low, medium, high, critical


# --- PII Pattern Registry ---
# Each pattern: (regex, category, severity, default_action)

PII_PATTERNS = [
    # Indian financial (CRITICAL — RBI regulated)
    (r'\b[A-Z]{5}\d{4}[A-Z]\b', 'pan_number', 'critical', Action.BLOCK),
    (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 'aadhaar', 'critical', Action.BLOCK),
    (r'\b[a-zA-Z0-9._-]+@[a-z]{2,6}\b', 'upi_id', 'high', Action.BLOCK),

    # Payment (CRITICAL — PCI-DSS)
    (r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
     'credit_card', 'critical', Action.BLOCK),

    # Global PII
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', 'email', 'medium', Action.REDACT),
    (r'\b(\+91[-\s]?)?[6-9]\d{9}\b', 'phone_india', 'medium', Action.REDACT),
    (r'\b(\+1[-\s]?)?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}\b', 'phone_us', 'medium', Action.REDACT),
    (r'\b\d{3}-\d{2}-\d{4}\b', 'ssn', 'critical', Action.BLOCK),

    # Secrets (HIGH — security breach)
    (r'\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b', 'aws_access_key', 'critical', Action.BLOCK),
    (r'\b(sk-|pk_live_|rk_live_)[a-zA-Z0-9]{20,}\b', 'api_key', 'high', Action.BLOCK),
    (r'\b(ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{36,}\b', 'github_token', 'high', Action.BLOCK),

    # IP Addresses
    (r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b',
     'ip_address', 'low', Action.REDACT),
]


# --- Scanner ---

class PIIScanner:
    """High-performance PII scanner for LLM request/response filtering."""

    def __init__(self, custom_patterns: list = None):
        self._patterns = []
        for pattern, category, severity, action in PII_PATTERNS:
            self._patterns.append((
                re.compile(pattern, re.IGNORECASE if category in ('email', 'ip_address') else 0),
                category, severity, action,
            ))

        # Add custom patterns
        if custom_patterns:
            for p in custom_patterns:
                self._patterns.append((
                    re.compile(p["pattern"]), p["category"], p["severity"], Action(p["action"]),
                ))

        # Stats
        self.total_scanned = 0
        self.total_blocked = 0
        self.total_redacted = 0
        self.total_findings = 0

    def scan(self, text: str) -> tuple[Action, list[Finding]]:
        """Scan text for PII. Returns (action, findings).

        Performance target: <1ms for typical prompts (500 chars).
        """
        start = time.perf_counter_ns()
        self.total_scanned += 1
        findings: list[Finding] = []
        worst_action = Action.ALLOW

        for compiled, category, severity, action in self._patterns:
            for match in compiled.finditer(text):
                finding = Finding(
                    category=category,
                    matched=match.group(),
                    position=(match.start(), match.end()),
                    action=action,
                    severity=severity,
                )
                findings.append(finding)
                if action == Action.BLOCK:
                    worst_action = Action.BLOCK
                elif action == Action.REDACT and worst_action != Action.BLOCK:
                    worst_action = Action.REDACT

        self.total_findings += len(findings)
        if worst_action == Action.BLOCK:
            self.total_blocked += 1
        elif worst_action == Action.REDACT:
            self.total_redacted += 1

        elapsed_us = (time.perf_counter_ns() - start) / 1000
        return worst_action, findings

    def redact(self, text: str) -> str:
        """Replace all PII with redaction markers."""
        redacted = text
        # Sort by position descending to replace from end (preserves positions)
        _, findings = self.scan(redacted)
        for f in sorted(findings, key=lambda x: x.position[0], reverse=True):
            start, end = f.position
            redacted = redacted[:start] + f"[REDACTED:{f.category.upper()}]" + redacted[end:]
        return redacted

    def scan_messages(self, messages: list[dict]) -> tuple[Action, list[Finding]]:
        """Scan all messages in a conversation."""
        all_findings = []
        worst_action = Action.ALLOW

        for msg in messages:
            content = msg.get("content", "")
            if not content:
                continue
            action, findings = self.scan(content)
            all_findings.extend(findings)
            if action == Action.BLOCK:
                worst_action = Action.BLOCK
            elif action == Action.REDACT and worst_action != Action.BLOCK:
                worst_action = Action.REDACT

        return worst_action, all_findings


# --- Demo / Exercise ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 4.1: PII Scanner")
    print("  Detect & redact sensitive data before it reaches LLM providers")
    print("=" * 70)

    scanner = PIIScanner()

    # Test cases (real patterns fintechs encounter)
    test_cases = [
        {
            "name": "✅ Clean request",
            "text": "What are the risk factors for credit line default in UPI transactions?",
        },
        {
            "name": "🚨 PAN + Aadhaar (RBI violation if sent to US servers)",
            "text": "Check credit score for PAN ABCPD1234E, Aadhaar 9876-5432-1098",
        },
        {
            "name": "🚨 Credit card number (PCI-DSS violation)",
            "text": "Customer reported fraud on card 4111-1111-1111-1111, please investigate",
        },
        {
            "name": "⚠️  Email + phone (redactable PII)",
            "text": "Send loan approval to rahul.sharma@company.com, phone +91-9876543210",
        },
        {
            "name": "🚨 AWS credentials in prompt (security breach)",
            "text": "Deploy to AWS using access key AKIAIOSFODNN7EXAMPLE, check the S3 bucket",
        },
        {
            "name": "🚨 Mixed: email + PAN + API key",
            "text": "User admin@vegapay.in with PAN BZCPS1234D called API with key sk-proj-abc123def456ghi789jkl012mno",
        },
    ]

    print()
    for tc in test_cases:
        action, findings = scanner.scan(tc["text"])

        # Color-code the output
        if action == Action.BLOCK:
            status = "🚫 BLOCKED"
        elif action == Action.REDACT:
            status = "✏️  REDACT"
        else:
            status = "✅ ALLOW"

        print(f"  {tc['name']}")
        print(f"  Input: \"{tc['text'][:80]}{'...' if len(tc['text']) > 80 else ''}\"")
        print(f"  Result: {status}")
        if findings:
            for f in findings:
                print(f"    → {f.severity.upper():8s} | {f.category:15s} | \"{f.matched}\"")
        if action == Action.REDACT:
            print(f"  Redacted: \"{scanner.redact(tc['text'])}\"")
        print()

    # Performance benchmark
    print("─" * 70)
    print("  PERFORMANCE BENCHMARK")
    print("─" * 70)
    sample_text = "Check credit for PAN ABCPD1234E, email test@co.com, card 4111-1111-1111-1111"
    iterations = 10000
    start = time.perf_counter()
    for _ in range(iterations):
        scanner.scan(sample_text)
    elapsed = time.perf_counter() - start
    print(f"  {iterations:,} scans in {elapsed:.3f}s")
    print(f"  Average: {elapsed/iterations*1_000_000:.1f} μs per scan")
    print(f"  Throughput: {iterations/elapsed:,.0f} scans/sec")
    print()
    print(f"  Total stats: scanned={scanner.total_scanned}, blocked={scanner.total_blocked}, redacted={scanner.total_redacted}")
