"""Lab 6.3: Agent Loop Detection — Kill Runaway Agents

Detect and terminate agents stuck in infinite loops before they burn budget.
Real incident: an agent looped 47 times calling the same tool, costing $340.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class AgentStep:
    step_num: int
    action: str
    tool: str
    input_hash: str
    tokens_used: int
    timestamp: float = field(default_factory=time.time)


class LoopDetector:
    """Detect agent loops using multiple heuristics."""

    def __init__(self, max_steps: int = 15, max_repeated_actions: int = 3, max_tokens: int = 50000):
        self.max_steps = max_steps
        self.max_repeated = max_repeated_actions
        self.max_tokens = max_tokens

    def check(self, steps: list[AgentStep]) -> tuple[bool, str]:
        """Check if agent is in a loop. Returns (should_kill, reason)."""
        # Check 1: Max steps exceeded
        if len(steps) >= self.max_steps:
            return True, f"Max steps ({self.max_steps}) exceeded"

        # Check 2: Same action repeated
        if len(steps) >= self.max_repeated:
            recent = steps[-self.max_repeated:]
            actions = [f"{s.tool}:{s.input_hash}" for s in recent]
            if len(set(actions)) == 1:
                return True, f"Same action repeated {self.max_repeated}x: {recent[0].tool}"

        # Check 3: Token budget exceeded
        total_tokens = sum(s.tokens_used for s in steps)
        if total_tokens > self.max_tokens:
            return True, f"Token budget exceeded ({total_tokens:,} > {self.max_tokens:,})"

        # Check 4: Oscillation pattern (A→B→A→B)
        if len(steps) >= 4:
            last4 = [f"{s.tool}:{s.action}" for s in steps[-4:]]
            if last4[0] == last4[2] and last4[1] == last4[3] and last4[0] != last4[1]:
                return True, f"Oscillation detected: {steps[-4].tool} ↔ {steps[-3].tool}"

        # Check 5: No progress (output similarity)
        if len(steps) >= 5:
            recent_hashes = [s.input_hash for s in steps[-5:]]
            unique = len(set(recent_hashes))
            if unique <= 2:
                return True, f"No progress: only {unique} unique actions in last 5 steps"

        return False, "OK"


class GuardedAgent:
    """Agent wrapper with loop detection and kill switch."""

    def __init__(self, name: str, detector: LoopDetector = None):
        self.name = name
        self.detector = detector or LoopDetector()
        self.steps: list[AgentStep] = []
        self.killed = False
        self.kill_reason = ""

    def step(self, action: str, tool: str, input_text: str, tokens: int = 500) -> bool:
        """Record a step. Returns False if agent should be killed."""
        input_hash = str(hash(input_text) % 10000)
        self.steps.append(AgentStep(
            step_num=len(self.steps) + 1,
            action=action, tool=tool,
            input_hash=input_hash, tokens_used=tokens,
        ))

        should_kill, reason = self.detector.check(self.steps)
        if should_kill:
            self.killed = True
            self.kill_reason = reason
            return False
        return True


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 6.3: Agent Loop Detection")
    print("  Kill runaway agents before they burn budget")
    print("=" * 70)
    print()

    # Scenario 1: Normal agent (completes successfully)
    print("  SCENARIO 1: Normal agent (diverse actions)")
    print("  " + "─" * 60)
    agent1 = GuardedAgent("normal-agent")
    actions = [
        ("search", "web_search", "kubernetes scaling"),
        ("read", "file_read", "deployment.yaml"),
        ("analyze", "llm_call", "analyze config"),
        ("write", "file_write", "updated config"),
        ("verify", "test_run", "run tests"),
    ]
    for action, tool, input_text in actions:
        alive = agent1.step(action, tool, input_text)
        status = "✓" if alive else "💀"
        print(f"    {status} Step {len(agent1.steps)}: {tool} → {action}")
    print(f"    Result: {'Completed ✅' if not agent1.killed else f'KILLED: {agent1.kill_reason}'}")

    # Scenario 2: Infinite loop (same action repeated)
    print(f"\n  SCENARIO 2: Infinite loop (repeating same search)")
    print("  " + "─" * 60)
    agent2 = GuardedAgent("looping-agent", LoopDetector(max_repeated_actions=3))
    for i in range(5):
        alive = agent2.step("search", "web_search", "fix deployment error")
        status = "✓" if alive else "💀"
        print(f"    {status} Step {i+1}: web_search → 'fix deployment error'")
        if not alive:
            break
    print(f"    Result: KILLED 🚫 — {agent2.kill_reason}")
    print(f"    Tokens saved: ~{(15 - len(agent2.steps)) * 500:,} (prevented {15 - len(agent2.steps)} more steps)")

    # Scenario 3: Oscillation
    print(f"\n  SCENARIO 3: Oscillation (search ↔ retry loop)")
    print("  " + "─" * 60)
    agent3 = GuardedAgent("oscillating-agent")
    oscillation = [
        ("search", "web_search", "find answer"),
        ("retry", "llm_call", "try again"),
        ("search", "web_search", "find answer"),
        ("retry", "llm_call", "try again"),
        ("search", "web_search", "find answer"),
    ]
    for action, tool, input_text in oscillation:
        alive = agent3.step(action, tool, input_text)
        status = "✓" if alive else "💀"
        print(f"    {status} Step {len(agent3.steps)}: {tool} → {action}")
        if not alive:
            break
    print(f"    Result: KILLED 🚫 — {agent3.kill_reason}")

    # Scenario 4: Budget exceeded
    print(f"\n  SCENARIO 4: Token budget explosion")
    print("  " + "─" * 60)
    agent4 = GuardedAgent("expensive-agent", LoopDetector(max_tokens=5000))
    for i in range(10):
        alive = agent4.step("generate", "llm_call", f"task {i}", tokens=2000)
        total = sum(s.tokens_used for s in agent4.steps)
        status = "✓" if alive else "💀"
        print(f"    {status} Step {i+1}: 2000 tokens (total: {total:,})")
        if not alive:
            break
    print(f"    Result: KILLED 🚫 — {agent4.kill_reason}")

    print(f"\n  ✅ Loop detection prevents runaway costs and stuck agents")
