"""
router.py — 40 lines of glue. This is the entire "agent framework."
Config does the heavy lifting. This just wires it together.
"""
import yaml
from litellm import completion

# Load config (the brain of the system)
with open("config.yaml") as f:
    config = yaml.safe_load(f)

def classify_intent(message: str) -> str:
    """Match keywords to find intent. No LLM needed for this."""
    msg_lower = message.lower()
    for intent, rules in config["intent_rules"].items():
        if any(kw in msg_lower for kw in rules["keywords"]):
            return intent
    return "default"

def route(message: str, team: str = "default") -> dict:
    """Route a message to the right model based on intent."""
    intent = classify_intent(message)
    route_config = config["routes"][intent]

    # Check team budget
    budget = config.get("budgets", {}).get(team, {})
    if budget and route_config["model"] not in budget.get("models_allowed", [route_config["model"]]):
        route_config = config["routes"]["default"]  # Fallback to cheap model

    response = completion(
        model=route_config["model"],
        messages=[
            {"role": "system", "content": route_config.get("system_prompt", "You are helpful.")},
            {"role": "user", "content": message},
        ],
        temperature=route_config["temperature"],
        max_tokens=route_config["max_tokens"],
    )

    return {
        "intent": intent,
        "model_used": route_config["model"],
        "response": response.choices[0].message.content,
        "reason": route_config.get("reason", ""),
    }

if __name__ == "__main__":
    # Demo: same router, different inputs → different models
    queries = [
        ("Should we approve a ₹5L credit limit for this applicant?", "lending_team"),
        ("How do I reset my password?", "support_team"),
        ("Suspicious pattern: 3 transactions from different IPs in 2 minutes", "fraud_team"),
        ("Extract PAN number from this document", "lending_team"),
    ]
    for query, team in queries:
        result = route(query, team)
        print(f"  [{result['intent']}] → {result['model_used']}")
        print(f"    Q: {query[:60]}")
        print(f"    Reason: {result['reason']}")
        print()
