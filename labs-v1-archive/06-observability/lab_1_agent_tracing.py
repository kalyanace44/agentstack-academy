"""Lab 6.1: Agent Execution Tracing

Build a tracing system that captures the full execution of an AI agent:
- Every LLM call (model, tokens, latency, cost)
- Every tool invocation (name, input, output, duration)
- Reasoning steps and decisions
- Parent-child relationships (agent → sub-agent)

This is what LangSmith/Arize do — we build it from scratch.
"""
from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


# --- Trace data model ---

@dataclass
class Span:
    """A single operation within a trace."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_id: str | None = None
    name: str = ""
    span_type: str = "generic"  # llm, tool, agent, retrieval
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "ok"  # ok, error
    # LLM-specific
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    # Tool-specific
    tool_name: str = ""
    tool_input: str = ""
    tool_output: str = ""
    # Metadata
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "name": self.name,
            "type": self.span_type,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "model": self.model or None,
            "tokens": (self.input_tokens + self.output_tokens) or None,
            "cost_usd": self.cost_usd or None,
            "tool": self.tool_name or None,
        }


@dataclass
class Trace:
    """A complete execution trace of an agent run."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    spans: list[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000

    @property
    def total_tokens(self) -> int:
        return sum(s.input_tokens + s.output_tokens for s in self.spans)

    @property
    def total_cost(self) -> float:
        return sum(s.cost_usd for s in self.spans)

    @property
    def llm_calls(self) -> int:
        return len([s for s in self.spans if s.span_type == "llm"])

    @property
    def tool_calls(self) -> int:
        return len([s for s in self.spans if s.span_type == "tool"])

    def summary(self) -> dict:
        return {
            "trace_id": self.id,
            "name": self.name,
            "duration_ms": round(self.duration_ms, 2),
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "spans": len(self.spans),
            "status": "error" if any(s.status == "error" for s in self.spans) else "ok",
        }


# --- Tracer (context-managed) ---

class Tracer:
    """Production-grade agent tracer.

    Usage:
        tracer = Tracer()
        with tracer.trace("credit_scoring_agent") as t:
            with tracer.span("llm_call", span_type="llm") as s:
                # ... make LLM call ...
                s.model = "gpt-4o"
                s.input_tokens = 500
                s.output_tokens = 200
    """

    def __init__(self):
        self.traces: list[Trace] = []
        self._current_trace: Trace | None = None
        self._current_span: Span | None = None

    @contextmanager
    def trace(self, name: str, **metadata):
        """Start a new trace (top-level agent execution)."""
        t = Trace(name=name, metadata=metadata)
        self._current_trace = t
        try:
            yield t
        except Exception as e:
            t.metadata["error"] = str(e)
        finally:
            t.end_time = time.time()
            self.traces.append(t)
            self._current_trace = None

    @contextmanager
    def span(self, name: str, span_type: str = "generic", **metadata):
        """Start a span within the current trace."""
        s = Span(
            name=name,
            span_type=span_type,
            start_time=time.time(),
            parent_id=self._current_span.id if self._current_span else None,
            metadata=metadata,
        )
        parent = self._current_span
        self._current_span = s
        try:
            yield s
        except Exception as e:
            s.status = "error"
            s.metadata["error"] = str(e)
        finally:
            s.end_time = time.time()
            if self._current_trace:
                self._current_trace.spans.append(s)
            self._current_span = parent


# --- Demo: Trace a full agent execution ---

def simulate_agent_run(tracer: Tracer):
    """Simulate a credit scoring agent processing a request."""

    with tracer.trace("credit_scoring_agent", team="lending", user_id="u_7834") as t:

        # Step 1: Parse request (LLM call)
        with tracer.span("parse_request", span_type="llm") as s:
            time.sleep(0.05)  # Simulate LLM latency
            s.model = "gpt-4o-mini"
            s.input_tokens = 150
            s.output_tokens = 80
            s.cost_usd = 0.000045

        # Step 2: Retrieve customer data (tool call)
        with tracer.span("fetch_customer_data", span_type="tool") as s:
            time.sleep(0.02)  # Simulate DB query
            s.tool_name = "database_query"
            s.tool_input = "SELECT * FROM customers WHERE id = 'c_9012'"
            s.tool_output = '{"name": "Rahul", "income": 150000, "credit_score": 720}'

        # Step 3: Retrieve credit bureau data (tool call)
        with tracer.span("credit_bureau_check", span_type="tool") as s:
            time.sleep(0.1)  # Simulate external API
            s.tool_name = "credit_bureau_api"
            s.tool_input = '{"pan": "REDACTED"}'
            s.tool_output = '{"score": 720, "accounts": 3, "defaults": 0}'

        # Step 4: RAG retrieval (retrieval span)
        with tracer.span("policy_retrieval", span_type="retrieval") as s:
            time.sleep(0.03)
            s.metadata["query"] = "credit line eligibility criteria income 1.5L"
            s.metadata["chunks_retrieved"] = 3
            s.metadata["top_score"] = 0.87

        # Step 5: Risk assessment (LLM call — expensive model)
        with tracer.span("risk_assessment", span_type="llm") as s:
            time.sleep(0.2)  # GPT-4 is slower
            s.model = "gpt-4o"
            s.input_tokens = 1200
            s.output_tokens = 350
            s.cost_usd = 0.0065

        # Step 6: Generate decision (LLM call)
        with tracer.span("generate_decision", span_type="llm") as s:
            time.sleep(0.08)
            s.model = "gpt-4o-mini"
            s.input_tokens = 400
            s.output_tokens = 150
            s.cost_usd = 0.00015

        # Step 7: Log to audit trail (tool call)
        with tracer.span("audit_log", span_type="tool") as s:
            time.sleep(0.01)
            s.tool_name = "compliance_logger"
            s.tool_input = '{"decision": "approved", "limit": 500000}'
            s.tool_output = '{"logged": true, "entry_id": "aud_3847"}'


# --- Main ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 6.1: Agent Execution Tracing")
    print("  Full observability for AI agent pipelines")
    print("=" * 70)
    print()

    tracer = Tracer()

    # Run the agent
    print("  🚀 Executing credit scoring agent...")
    simulate_agent_run(tracer)

    # Display trace
    trace = tracer.traces[0]
    print(f"\n  {'─' * 66}")
    print(f"  TRACE: {trace.name}")
    print(f"  ID: {trace.id}")
    print(f"  Duration: {trace.duration_ms:.1f}ms")
    print(f"  {'─' * 66}")
    print()

    # Waterfall view
    print("  ┌─ WATERFALL VIEW ─────────────────────────────────────────────────┐")
    print(f"  │ {'Span':<25} {'Type':<12} {'Duration':>10} {'Tokens':>8} {'Cost':>10} │")
    print(f"  ├{'─'*70}┤")
    for span in trace.spans:
        tokens = span.input_tokens + span.output_tokens
        cost = f"${span.cost_usd:.5f}" if span.cost_usd else "—"
        bar_len = int(span.duration_ms / trace.duration_ms * 30)
        bar = "█" * max(1, bar_len)
        print(f"  │ {span.name:<25} {span.span_type:<12} {span.duration_ms:>7.1f}ms {tokens or '—':>8} {cost:>10} │")
        print(f"  │ {'':25} {bar}")
    print(f"  └{'─'*70}┘")

    # Summary
    summary = trace.summary()
    print(f"\n  📊 TRACE SUMMARY")
    print(f"  ├─ Total duration:  {summary['duration_ms']:.1f}ms")
    print(f"  ├─ LLM calls:       {summary['llm_calls']} (where the money goes)")
    print(f"  ├─ Tool calls:      {summary['tool_calls']}")
    print(f"  ├─ Total tokens:    {summary['total_tokens']:,}")
    print(f"  ├─ Total cost:      ${summary['total_cost_usd']:.6f}")
    print(f"  └─ Status:          {summary['status']}")

    # Cost breakdown
    print(f"\n  💰 COST BREAKDOWN BY MODEL")
    model_costs: dict[str, float] = {}
    for span in trace.spans:
        if span.model:
            model_costs[span.model] = model_costs.get(span.model, 0) + span.cost_usd
    for model, cost in sorted(model_costs.items(), key=lambda x: -x[1]):
        pct = cost / trace.total_cost * 100
        print(f"  ├─ {model:<25} ${cost:.6f}  ({pct:.0f}%)")

    # Insights
    print(f"\n  💡 INSIGHTS")
    slowest = max(trace.spans, key=lambda s: s.duration_ms)
    print(f"  • Slowest span: {slowest.name} ({slowest.duration_ms:.0f}ms) — optimize this first")
    print(f"  • LLM latency: {sum(s.duration_ms for s in trace.spans if s.span_type == 'llm'):.0f}ms ({sum(s.duration_ms for s in trace.spans if s.span_type == 'llm') / trace.duration_ms * 100:.0f}% of total)")
    print(f"  • 92% of cost is from ONE gpt-4o call — consider if gpt-4o-mini works here")
