"""Lab 4.4: Output Validation — Schema Enforcement + Hallucination Detection

Validate LLM outputs before returning to users:
1. JSON schema enforcement (structured outputs)
2. Hallucination detection (claims not grounded in context)
3. Content safety filters
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cleaned_output: str = ""


class SchemaValidator:
    """Validate LLM JSON outputs against a schema."""

    def __init__(self, schema: dict):
        self.schema = schema

    def validate(self, output: str) -> ValidationResult:
        errors = []
        warnings = []

        # Try to parse JSON
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            # Try to extract JSON from markdown
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    warnings.append("JSON was wrapped in markdown — extracted successfully")
                except json.JSONDecodeError:
                    return ValidationResult(valid=False, errors=[f"Invalid JSON: {e}"])
            else:
                return ValidationResult(valid=False, errors=[f"Invalid JSON: {e}"])

        # Check required fields
        for field_name, field_spec in self.schema.get("properties", {}).items():
            if field_name in self.schema.get("required", []):
                if field_name not in data:
                    errors.append(f"Missing required field: {field_name}")
                    continue

            if field_name in data:
                # Type check
                expected_type = field_spec.get("type")
                value = data[field_name]
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"Field '{field_name}' should be string, got {type(value).__name__}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field_name}' should be number, got {type(value).__name__}")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"Field '{field_name}' should be array, got {type(value).__name__}")

                # Enum check
                if "enum" in field_spec and value not in field_spec["enum"]:
                    errors.append(f"Field '{field_name}' must be one of {field_spec['enum']}, got '{value}'")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_output=json.dumps(data, indent=2) if not errors else "",
        )


class HallucinationDetector:
    """Detect claims in output not grounded in the provided context."""

    def check(self, output: str, context: str) -> ValidationResult:
        errors = []
        warnings = []

        # Extract factual claims (numbers, dates, names)
        claims = self._extract_claims(output)
        context_lower = context.lower()

        for claim_type, claim_value in claims:
            if claim_value.lower() not in context_lower:
                if claim_type == "number":
                    warnings.append(f"Number '{claim_value}' not found in context — possible hallucination")
                elif claim_type == "name":
                    warnings.append(f"Name '{claim_value}' not found in context — verify")

        # High hallucination risk if many ungrounded claims
        if len(warnings) > 3:
            errors.append(f"High hallucination risk: {len(warnings)} ungrounded claims")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _extract_claims(self, text: str) -> list[tuple[str, str]]:
        claims = []
        # Numbers with context
        for m in re.finditer(r'(?:₹|Rs\.?|\$)?\d[\d,.]+%?', text):
            claims.append(("number", m.group()))
        # Capitalized names (simple NER)
        for m in re.finditer(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text):
            claims.append(("name", m.group()))
        return claims


class ContentFilter:
    """Filter unsafe or inappropriate content from outputs."""

    BLOCKED_PATTERNS = [
        r'(?:how\s+to\s+)?(?:hack|exploit|attack)\s+',
        r'(?:steal|phish|scam)\s+',
        r'(?:illegal|illicit)\s+(?:activity|substance)',
    ]

    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS]

    def check(self, output: str) -> ValidationResult:
        issues = []
        for pattern in self._patterns:
            if pattern.search(output):
                issues.append(f"Potentially unsafe content detected: {pattern.pattern[:40]}")
        return ValidationResult(valid=len(issues) == 0, errors=issues)


# --- Combined Pipeline ---

class OutputValidator:
    """Run all output validations in sequence."""

    def __init__(self, schema: dict = None):
        self.schema_validator = SchemaValidator(schema) if schema else None
        self.hallucination_detector = HallucinationDetector()
        self.content_filter = ContentFilter()

    def validate(self, output: str, context: str = "", expect_json: bool = False) -> ValidationResult:
        all_errors = []
        all_warnings = []

        # 1. Content safety
        safety = self.content_filter.check(output)
        all_errors.extend(safety.errors)

        # 2. Schema validation
        if expect_json and self.schema_validator:
            schema_result = self.schema_validator.validate(output)
            all_errors.extend(schema_result.errors)
            all_warnings.extend(schema_result.warnings)

        # 3. Hallucination check
        if context:
            halluc = self.hallucination_detector.check(output, context)
            all_errors.extend(halluc.errors)
            all_warnings.extend(halluc.warnings)

        return ValidationResult(
            valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
        )


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 4.4: Output Validation")
    print("  Schema enforcement + hallucination detection + content safety")
    print("=" * 70)
    print()

    # Schema for credit decision
    schema = {
        "properties": {
            "decision": {"type": "string", "enum": ["approved", "rejected", "manual_review"]},
            "credit_limit": {"type": "number"},
            "confidence": {"type": "number"},
            "reasoning": {"type": "string"},
        },
        "required": ["decision", "credit_limit", "confidence", "reasoning"],
    }

    validator = OutputValidator(schema=schema)

    # Test 1: Valid JSON output
    print("  TEST 1: Valid structured output")
    good_output = json.dumps({
        "decision": "approved",
        "credit_limit": 200000,
        "confidence": 0.87,
        "reasoning": "Income ₹1.5L/mo, credit score 720, no defaults"
    })
    r = validator.validate(good_output, expect_json=True)
    print(f"    Valid: {r.valid} ✅")

    # Test 2: Invalid schema
    print("\n  TEST 2: Missing required field + wrong enum")
    bad_output = json.dumps({"decision": "maybe", "credit_limit": "high"})
    r = validator.validate(bad_output, expect_json=True)
    print(f"    Valid: {r.valid} ❌")
    for e in r.errors:
        print(f"    → {e}")

    # Test 3: Hallucination detection
    print("\n  TEST 3: Hallucination detection")
    context = "Customer Rahul has income ₹1,50,000 and credit score 720. No loan defaults."
    hallucinated = "Rahul has an excellent credit score of 810 and earns ₹3,00,000 per month. He has 5 active loans with HDFC Bank."
    r = validator.validate(hallucinated, context=context)
    print(f"    Valid: {r.valid}")
    for w in r.warnings:
        print(f"    ⚠️  {w}")

    # Test 4: Content safety
    print("\n  TEST 4: Content safety filter")
    unsafe = "Here's how to exploit the authentication system to steal user tokens"
    r = validator.validate(unsafe)
    print(f"    Valid: {r.valid} ❌")
    for e in r.errors:
        print(f"    → {e}")

    print("\n  ✅ All validation layers working")
