"""
cost_router.py — Route requests by complexity. Config controls everything.
"""
import re
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

routing = config["routing"]
budget = config["budget"]


def classify_request(prompt: str) -> tuple[str, dict]:
    """Classify prompt into cost tier based on rules."""
    prompt_lower = prompt.lower().strip()
    input_length = len(prompt_lower.split())

    for tier_name, tier in routing.items():
        match_rules = tier["match"]

        # Check keywords (exact word match)
        if "keywords" in match_rules:
            words = set(prompt_lower.split())
            if words & set(match_rules["keywords"]):
                return tier_name, tier

        # Check max input length
        if "max_input_length" in match_rules:
            if input_length > match_rules["max_input_length"]:
                continue

        # Check patterns (regex)
        if "patterns" in match_rules:
            for pattern in match_rules["patterns"]:
                if re.search(pattern, prompt_lower):
                    return tier_name, tier

    # Default to medium
    return "medium", routing["medium"]


def estimate_cost(tier: dict, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a request."""
    total_tokens = input_tokens + output_tokens
    return (total_tokens / 1000) * tier["cost_per_1k_tokens"]


if __name__ == "__main__":
    test_prompts = [
        "hello",
        "How to set up Kubernetes?",
        "Analyze this codebase for security vulnerabilities and architect a fix",
        "Check this transaction for fraud indicators",
        "thanks",
        "Write a function to parse JSON in Python",
        "What is Docker?",
        "Review code for the payment service and debug the timeout issue",
    ]

    print("═" * 70)
    print("  Cost Router — Smart Model Selection")
    print("═" * 70)
    print(f"  {'Prompt':<45} {'Tier':<10} {'Model':<15} {'Est. Cost'}")
    print(f"  {'─'*45} {'─'*10} {'─'*15} {'─'*10}")

    total_smart = 0.0
    total_naive = 0.0
    naive_cost = 0.005  # gpt-4o cost per 1k tokens

    for prompt in test_prompts:
        tier_name, tier = classify_request(prompt)
        # Estimate: avg 50 input + tier max_tokens output
        cost = estimate_cost(tier, 50, tier["max_tokens"])
        naive = (50 + 2000) / 1000 * naive_cost  # Naive: all gpt-4o, 2000 tokens

        total_smart += cost
        total_naive += naive

        display = prompt[:43] + ".." if len(prompt) > 45 else prompt
        print(f"  {display:<45} {tier_name:<10} {tier['model']:<15} ${cost:.4f}")

    print(f"\n  {'═'*70}")
    print(f"  💰 Smart routing total:  ${total_smart:.4f}")
    print(f"  💸 Naive (all gpt-4o):   ${total_naive:.4f}")
    savings_pct = (1 - total_smart / total_naive) * 100 if total_naive > 0 else 0
    print(f"  📉 Savings:              {savings_pct:.0f}%")
    print(f"\n  At 10K requests/day:")
    print(f"    Naive:  ${total_naive/len(test_prompts)*10000:.0f}/day (${total_naive/len(test_prompts)*300000:.0f}/month)")
    print(f"    Smart:  ${total_smart/len(test_prompts)*10000:.0f}/day (${total_smart/len(test_prompts)*300000:.0f}/month)")
