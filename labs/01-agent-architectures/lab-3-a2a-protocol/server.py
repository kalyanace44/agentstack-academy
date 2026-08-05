"""
server.py — A2A-compliant agent server. 45 lines.
Each agent runs this with different config. The YAML defines what it does.
"""
import json
import yaml
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load agent config from environment or default
import sys
AGENT_ID = sys.argv[1] if len(sys.argv) > 1 else "credit_scorer"

with open("agents.yaml") as f:
    config = yaml.safe_load(f)

agent_config = config["agents"][AGENT_ID]

# Build Agent Card (the A2A discovery manifest)
AGENT_CARD = {
    "name": agent_config["name"],
    "description": agent_config["description"],
    "url": agent_config["url"],
    "version": agent_config["version"],
    "skills": agent_config["skills"],
}


class A2AHandler(BaseHTTPRequestHandler):
    """Minimal A2A-compliant handler."""

    def do_GET(self):
        # Discovery endpoint
        if self.path == "/.well-known/agent.json":
            self.respond(200, AGENT_CARD)
        elif self.path == "/health":
            self.respond(200, {"status": "healthy", "agent": AGENT_ID})
        else:
            self.respond(404, {"error": "not found"})

    def do_POST(self):
        # Task submission endpoint
        if self.path == "/tasks":
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            result = handle_task(body)
            self.respond(200, result)
        else:
            self.respond(404, {"error": "not found"})

    def respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def log_message(self, format, *args):
        pass  # Suppress logs for demo


def handle_task(task: dict) -> dict:
    """Process a task based on skill. This is where your logic goes."""
    skill = task.get("skill", "")
    data = task.get("data", {})

    if skill == "credit_score":
        income = data.get("income", 0)
        history = data.get("credit_history_years", 0)
        risk = max(0, min(100, 100 - (income / 5000 + history * 3)))
        return {"state": "completed", "result": {
            "risk_score": round(risk, 1),
            "approved": risk < 60,
            "credit_limit": int(income * 6 * (1 - risk/100)) if risk < 60 else 0,
        }}

    elif skill == "fraud_check":
        signals = []
        score = 0.0
        if data.get("income", 0) > 1_000_000:
            signals.append("Unusually high income"); score += 0.4
        if data.get("address_changes", 0) > 3:
            signals.append("High address churn"); score += 0.3
        return {"state": "completed", "result": {
            "fraud_score": round(min(1.0, score), 2),
            "signals": signals,
            "block": score > 0.5,
        }}

    elif skill == "verify_identity":
        doc_num = data.get("document_number", "")
        valid = bool(re.match(r"[A-Z]{5}\d{4}[A-Z]", doc_num))  # PAN format
        return {"state": "completed", "result": {
            "verified": valid,
            "match_score": 0.95 if valid else 0.0,
            "issues": [] if valid else ["Document format invalid"],
        }}

    return {"state": "failed", "error": f"Unknown skill: {skill}"}


if __name__ == "__main__":
    port = int(agent_config["url"].split(":")[-1])
    print(f"  🤖 {agent_config['name']} listening on :{port}")
    HTTPServer(("", port), A2AHandler).serve_forever()
