"""
orchestrator.py — Discover agents by skill, delegate tasks.
30 lines of glue. Config defines the pipeline.
"""
import json
import yaml
import urllib.request

with open("agents.yaml") as f:
    config = yaml.safe_load(f)

def discover(skill: str) -> dict | None:
    """Find an agent that has this skill (check each registered agent)."""
    for agent_id, agent in config["agents"].items():
        for s in agent["skills"]:
            if s["id"] == skill:
                return agent
    return None

def delegate(agent_url: str, skill: str, data: dict) -> dict:
    """Send a task to an agent via A2A protocol."""
    task = json.dumps({"skill": skill, "data": data}).encode()
    req = urllib.request.Request(
        f"{agent_url}/tasks",
        data=task,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())
    except Exception as e:
        return {"state": "failed", "error": str(e)}

def run_pipeline(application: dict):
    """Run the orchestrator pipeline from config."""
    print(f"\n  🎯 Processing: {application.get('applicant_id', 'unknown')}")

    for step in config["orchestrator"]["pipeline"]:
        skill = step["skill"]
        on_fail = step.get("on_fail", "reject")

        # Discover
        agent = discover(skill)
        if not agent:
            print(f"    ❌ No agent found for skill: {skill}")
            return {"decision": "error", "reason": f"No agent for {skill}"}

        print(f"    → {skill} → {agent['name']} ({agent['url']})")

        # Delegate
        result = delegate(agent["url"], skill, application)

        if result.get("state") == "failed":
            print(f"    ← FAILED: {result.get('error')}")
            return {"decision": on_fail, "reason": result.get("error")}

        r = result.get("result", {})
        print(f"    ← {r}")

        # Check failure conditions
        if skill == "fraud_check" and r.get("block"):
            return {"decision": "rejected", "reason": f"Fraud: {r['signals']}"}
        if skill == "verify_identity" and not r.get("verified"):
            return {"decision": on_fail, "reason": f"KYC failed: {r['issues']}"}
        if skill == "credit_score" and not r.get("approved"):
            return {"decision": "rejected", "reason": f"Risk too high: {r['risk_score']}"}

    return {"decision": "approved", "reason": "All checks passed"}


if __name__ == "__main__":
    applications = [
        {"applicant_id": "APP-001", "income": 150000, "credit_history_years": 5,
         "defaults": 0, "address_changes": 1, "document_type": "PAN", "document_number": "ABCDE1234F", "name": "Rahul"},
        {"applicant_id": "APP-002", "income": 2000000, "credit_history_years": 2,
         "defaults": 0, "address_changes": 5, "document_type": "PAN", "document_number": "XYZAB5678C", "name": "Priya"},
        {"applicant_id": "APP-003", "income": 80000, "credit_history_years": 3,
         "defaults": 0, "address_changes": 1, "document_type": "PAN", "document_number": "INVALID", "name": "Amit"},
    ]

    print("═" * 60)
    print("  A2A Orchestrator — Delegating to Specialist Agents")
    print("═" * 60)

    for app in applications:
        result = run_pipeline(app)
        icon = "✅" if result["decision"] == "approved" else "❌"
        print(f"  {icon} {app['applicant_id']}: {result['decision']} — {result['reason']}")
