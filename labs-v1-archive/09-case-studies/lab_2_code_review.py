"""Lab 9.2: Code Review Agent — CI-Integrated, Multi-Repo

Architecture for an automated code review agent that:
- Runs on every PR via GitHub Actions
- Reviews for security, performance, correctness
- Posts inline comments on specific lines
- Learns from accepted/rejected suggestions

Scale: 500+ PRs/day across 20 repositories.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"    # Must fix: security, data loss
    WARNING = "warning"      # Should fix: performance, bugs
    SUGGESTION = "suggestion"  # Nice to have: style, readability
    PRAISE = "praise"        # Good patterns worth highlighting


@dataclass
class ReviewComment:
    file: str
    line: int
    severity: Severity
    category: str
    message: str
    suggestion: str = ""  # Suggested fix


@dataclass
class PRReview:
    pr_id: str
    repo: str
    files_reviewed: int = 0
    comments: list[ReviewComment] = field(default_factory=list)
    verdict: str = "approve"  # approve, request_changes, comment
    tokens_used: int = 0
    latency_ms: float = 0.0


class SecurityReviewer:
    """Check for security vulnerabilities."""
    
    PATTERNS = {
        "sql_injection": (r'f["\'].*(?:SELECT|INSERT|DELETE|UPDATE).*\{', Severity.CRITICAL),
        "hardcoded_secret": (r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', Severity.CRITICAL),
        "eval_usage": (r'\beval\s*\(', Severity.CRITICAL),
        "no_input_validation": (r'request\.(args|form|json)\[', Severity.WARNING),
        "http_not_https": (r'http://(?!localhost|127\.0\.0\.1)', Severity.WARNING),
    }

    def review(self, file: str, content: str) -> list[ReviewComment]:
        comments = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for vuln_type, (pattern, severity) in self.PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    comments.append(ReviewComment(
                        file=file, line=i, severity=severity,
                        category="security",
                        message=f"Potential {vuln_type.replace('_', ' ')}: {line.strip()[:60]}",
                        suggestion=self._suggest_fix(vuln_type, line),
                    ))
        return comments

    def _suggest_fix(self, vuln_type: str, line: str) -> str:
        fixes = {
            "sql_injection": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
            "hardcoded_secret": "Use environment variables: os.environ['SECRET_KEY']",
            "eval_usage": "Use ast.literal_eval() for safe evaluation, or avoid eval entirely",
            "no_input_validation": "Validate input: value = request.args.get('key', type=int)",
            "http_not_https": "Use HTTPS for all external connections",
        }
        return fixes.get(vuln_type, "")


class PerformanceReviewer:
    """Check for performance issues."""

    PATTERNS = {
        "n_plus_one": (r'for\s+\w+\s+in\s+\w+.*:\s*$', Severity.WARNING),
        "no_pagination": (r'\.all\(\)|\.find\(\{\}\)', Severity.WARNING),
        "sync_in_async": (r'(?:requests\.get|time\.sleep)\(', Severity.WARNING),
        "unbounded_list": (r'\[\s*\w+\s+for\s+\w+\s+in\s+\w+\s*\]', Severity.SUGGESTION),
    }

    def review(self, file: str, content: str) -> list[ReviewComment]:
        comments = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for issue, (pattern, severity) in self.PATTERNS.items():
                if re.search(pattern, line):
                    comments.append(ReviewComment(
                        file=file, line=i, severity=severity,
                        category="performance",
                        message=f"Potential {issue.replace('_', ' ')}: consider optimization",
                    ))
        return comments


class CodeReviewAgent:
    """Orchestrate multiple reviewers on a PR."""

    def __init__(self):
        self.security = SecurityReviewer()
        self.performance = PerformanceReviewer()
        self.reviews_completed = 0

    def review_pr(self, pr_id: str, repo: str, files: dict[str, str]) -> PRReview:
        """Review a complete PR (dict of filename → content)."""
        start = time.perf_counter()
        review = PRReview(pr_id=pr_id, repo=repo)

        for filename, content in files.items():
            review.files_reviewed += 1
            # Run all reviewers
            review.comments.extend(self.security.review(filename, content))
            review.comments.extend(self.performance.review(filename, content))

        # Determine verdict
        critical = sum(1 for c in review.comments if c.severity == Severity.CRITICAL)
        warnings = sum(1 for c in review.comments if c.severity == Severity.WARNING)

        if critical > 0:
            review.verdict = "request_changes"
        elif warnings > 2:
            review.verdict = "request_changes"
        elif warnings > 0:
            review.verdict = "comment"
        else:
            review.verdict = "approve"

        review.latency_ms = (time.perf_counter() - start) * 1000
        review.tokens_used = sum(len(content.split()) * 2 for content in files.values())
        self.reviews_completed += 1
        return review


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 9.2: Code Review Agent (CI-Integrated)")
    print("  Automated security + performance review on every PR")
    print("=" * 70)
    print()

    agent = CodeReviewAgent()

    # Simulate a PR with various issues
    pr_files = {
        "app/api/users.py": '''
from flask import request
import os

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    db.execute(query)
    return result

def create_user():
    data = request.json["username"]
    password = "admin123"
    return save_user(data, password)

def list_users():
    users = db.query(User).all()
    return jsonify(users)
''',
        "app/services/payment.py": '''
import requests
import time

async def process_payment(order_id):
    # Fetch order
    response = requests.get(f"http://api.payment.com/orders/{order_id}")
    time.sleep(2)  # Wait for processing
    return response.json()

API_SECRET = "sk_live_abc123xyz789"
''',
        "app/utils/helpers.py": '''
import ast

def safe_calculate(expression):
    return eval(expression)

def load_config(path):
    with open(path) as f:
        return ast.literal_eval(f.read())
''',
    }

    review = agent.review_pr("PR-142", "fintech-api", pr_files)

    print(f"  PR: #{review.pr_id} in {review.repo}")
    print(f"  Files reviewed: {review.files_reviewed}")
    print(f"  Verdict: {'🔴 REQUEST CHANGES' if review.verdict == 'request_changes' else '🟡 COMMENT' if review.verdict == 'comment' else '🟢 APPROVE'}")
    print(f"  Latency: {review.latency_ms:.1f}ms")
    print(f"  Tokens: {review.tokens_used}")
    print()

    # Display comments by severity
    for severity in [Severity.CRITICAL, Severity.WARNING, Severity.SUGGESTION]:
        comments = [c for c in review.comments if c.severity == severity]
        if comments:
            icon = "🔴" if severity == Severity.CRITICAL else "🟡" if severity == Severity.WARNING else "💡"
            print(f"  {icon} {severity.value.upper()} ({len(comments)}):")
            for c in comments:
                print(f"    {c.file}:{c.line} — {c.message}")
                if c.suggestion:
                    print(f"      💡 Fix: {c.suggestion}")
            print()

    print(f"  {'─' * 66}")
    print("  💡 PRODUCTION ARCHITECTURE:")
    print("    1. GitHub webhook → queue (handle burst of PRs)")
    print("    2. Worker pulls PR diff (only changed files, not full repo)")
    print("    3. Parallel review: security | performance | correctness | style")
    print("    4. Post inline comments via GitHub API")
    print("    5. Track accepted/rejected suggestions → improve over time")
    print("    6. Skip re-review if only docs/tests changed (smart filtering)")
