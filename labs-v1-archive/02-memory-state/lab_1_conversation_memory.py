"""Lab 2.1: Conversation Memory Strategies

Compare three memory strategies for agents:
1. Sliding Window — last N messages (simple, lossy)
2. Summary Memory — compressed summaries of old context (token-efficient)
3. Hybrid Buffer — recent messages + summary of older ones (best of both)

Demonstrates: trade-offs between context length, cost, and recall.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque


@dataclass
class Message:
    role: str      # user, assistant, system
    content: str
    tokens: int = 0

    def __post_init__(self):
        # Approximate token count (1 token ≈ 4 chars)
        if not self.tokens:
            self.tokens = len(self.content) // 4


# --- Strategy 1: Sliding Window ---

class SlidingWindowMemory:
    """Keep last N messages. Simple but forgets everything older.

    Pros: Simple, predictable token usage, fast
    Cons: Loses all context beyond window, bad for multi-session tasks
    Best for: Simple chatbots, one-shot tasks
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._messages: deque[Message] = deque(maxlen=window_size)

    def add(self, msg: Message):
        self._messages.append(msg)

    def get_context(self) -> list[Message]:
        return list(self._messages)

    @property
    def token_count(self) -> int:
        return sum(m.tokens for m in self._messages)

    @property
    def messages_stored(self) -> int:
        return len(self._messages)

    @property
    def messages_lost(self) -> int:
        return 0  # Can't track, it's a deque


# --- Strategy 2: Summary Memory ---

class SummaryMemory:
    """Summarize old messages into a compressed context.

    Pros: Captures long history in few tokens, good for multi-session
    Cons: Loses details, summary quality depends on LLM, adds latency
    Best for: Long conversations, customer support agents
    """

    def __init__(self, max_messages_before_summary: int = 6):
        self.max_before_summary = max_messages_before_summary
        self._recent: list[Message] = []
        self._summary: str = ""
        self._total_messages: int = 0
        self._summarize_count: int = 0

    def add(self, msg: Message):
        self._recent.append(msg)
        self._total_messages += 1

        if len(self._recent) > self.max_before_summary:
            self._compress()

    def _compress(self):
        """Summarize old messages into the running summary.
        In production, call an LLM here. We simulate it.
        """
        old = self._recent[:len(self._recent) - 2]  # Keep last 2
        self._recent = self._recent[-2:]

        # Simulated summary (in production: call GPT-3.5 with summarize prompt)
        topics = set()
        for m in old:
            words = m.content.lower().split()
            topics.update(w for w in words if len(w) > 5)

        new_summary = f"Previous discussion covered: {', '.join(list(topics)[:8])}"
        if self._summary:
            self._summary = f"{self._summary}. {new_summary}"
        else:
            self._summary = new_summary

        self._summarize_count += 1

    def get_context(self) -> list[Message]:
        context = []
        if self._summary:
            context.append(Message(role="system", content=f"[Conversation summary: {self._summary}]"))
        context.extend(self._recent)
        return context

    @property
    def token_count(self) -> int:
        summary_tokens = len(self._summary) // 4 if self._summary else 0
        return summary_tokens + sum(m.tokens for m in self._recent)


# --- Strategy 3: Hybrid Buffer ---

class HybridMemory:
    """Recent messages + summary of older ones. Best of both worlds.

    Keeps a fixed window of recent messages for detail,
    plus a compressed summary of everything before that.
    Token budget is bounded regardless of conversation length.

    Pros: Bounded tokens, retains both recent detail and long-term context
    Cons: More complex, summary still lossy
    Best for: Production agents, multi-step workflows, customer support
    """

    def __init__(self, recent_window: int = 6, max_token_budget: int = 2000):
        self.recent_window = recent_window
        self.max_token_budget = max_token_budget
        self._recent: deque[Message] = deque(maxlen=recent_window)
        self._summary: str = ""
        self._overflow_buffer: list[Message] = []
        self._total_messages: int = 0

    def add(self, msg: Message):
        self._total_messages += 1

        if len(self._recent) == self.recent_window:
            # Oldest message moves to overflow
            oldest = self._recent[0]
            self._overflow_buffer.append(oldest)

            # Compress overflow when it gets large
            if len(self._overflow_buffer) >= 4:
                self._compress_overflow()

        self._recent.append(msg)

    def _compress_overflow(self):
        """Compress overflow buffer into summary."""
        topics = set()
        for m in self._overflow_buffer:
            words = m.content.lower().split()
            topics.update(w for w in words if len(w) > 4 and w.isalpha())

        chunk_summary = f"Discussion included: {', '.join(list(topics)[:10])}"
        if self._summary:
            self._summary = f"{self._summary}; {chunk_summary}"
        else:
            self._summary = chunk_summary

        # Trim summary if too long
        if len(self._summary) > self.max_token_budget * 2:
            self._summary = self._summary[-(self.max_token_budget * 2):]

        self._overflow_buffer.clear()

    def get_context(self) -> list[Message]:
        context = []
        if self._summary:
            context.append(Message(role="system", content=f"[Prior context: {self._summary}]"))
        context.extend(self._recent)
        return context

    @property
    def token_count(self) -> int:
        summary_tokens = len(self._summary) // 4 if self._summary else 0
        recent_tokens = sum(m.tokens for m in self._recent)
        return summary_tokens + recent_tokens


# --- Comparison Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 2.1: Conversation Memory Strategies")
    print("  Compare: Sliding Window vs Summary vs Hybrid")
    print("=" * 70)
    print()

    # Initialize all three strategies
    sliding = SlidingWindowMemory(window_size=6)
    summary = SummaryMemory(max_messages_before_summary=6)
    hybrid = HybridMemory(recent_window=6, max_token_budget=500)

    # Simulate a 20-message conversation (typical support interaction)
    conversation = [
        ("user", "Hi, I need help with my credit line application"),
        ("assistant", "I'd be happy to help with your credit line application. What's the issue?"),
        ("user", "I submitted my PAN and Aadhaar documents last week but haven't heard back"),
        ("assistant", "Let me check the status of your application. Can you confirm your application ID?"),
        ("user", "It's APP-2024-7834"),
        ("assistant", "I found your application. It's currently in the KYC verification stage. The documents are being validated."),
        ("user", "How long does KYC usually take?"),
        ("assistant", "KYC verification typically takes 2-3 business days. Your documents were uploaded 5 days ago, which is slightly longer than usual."),
        ("user", "That's too long. Can you escalate this?"),
        ("assistant", "I'll escalate this to the KYC team immediately. They'll prioritize your application. You should hear back within 24 hours."),
        ("user", "Also, what's the credit limit I was approved for?"),
        ("assistant", "Based on your income documents and credit score, you were pre-approved for a ₹2,00,000 credit line with 18% APR."),
        ("user", "Can I get a higher limit? I have a salary of ₹1.5L per month"),
        ("assistant", "With ₹1.5L monthly income, you may qualify for up to ₹5,00,000. I'll submit a limit increase request along with the escalation."),
        ("user", "Great. One more thing — can I use the credit line for UPI payments?"),
        ("assistant", "Yes! Once approved, your credit line works as a UPI payment source. You can link it in any UPI app."),
        ("user", "What's the per-transaction limit on UPI?"),
        ("assistant", "UPI transactions from credit line are capped at ₹1,00,000 per transaction and ₹3,00,000 per day as per RBI guidelines."),
        ("user", "Perfect. So to summarize — you're escalating KYC, requesting higher limit, and I can use it for UPI?"),
        ("assistant", "Exactly! Three action items: 1) KYC escalation (response in 24h), 2) Limit increase to ₹5L (pending approval), 3) UPI activation once KYC clears."),
    ]

    print("  📝 Simulating 20-message conversation...\n")
    for role, content in conversation:
        msg = Message(role=role, content=content)
        sliding.add(msg)
        summary.add(msg)
        hybrid.add(msg)

    # Compare results
    print("  ┌────────────────────────────────────────────────────────────────┐")
    print("  │  COMPARISON AFTER 20 MESSAGES                                  │")
    print("  ├─────────────────┬──────────────┬───────────────┬───────────────┤")
    print("  │ Strategy        │ Tokens Used  │ Messages Kept │ Context Length│")
    print("  ├─────────────────┼──────────────┼───────────────┼───────────────┤")
    print(f"  │ Sliding Window  │ {sliding.token_count:>10}  │ {sliding.messages_stored:>11}  │ {len(sliding.get_context()):>11}  │")
    print(f"  │ Summary         │ {summary.token_count:>10}  │ {len(summary.get_context()):>11}  │ {len(summary.get_context()):>11}  │")
    print(f"  │ Hybrid          │ {hybrid.token_count:>10}  │ {len(hybrid.get_context()):>11}  │ {len(hybrid.get_context()):>11}  │")
    print("  └─────────────────┴──────────────┴───────────────┴───────────────┘")

    # Show what each strategy remembers
    print("\n  📋 What each strategy remembers:")
    print(f"\n  {'─' * 66}")
    print("  SLIDING WINDOW (last 6 messages):")
    for m in sliding.get_context()[-3:]:
        print(f"    [{m.role}] {m.content[:80]}...")

    print(f"\n  {'─' * 66}")
    print("  SUMMARY MEMORY:")
    for m in summary.get_context()[:2]:
        print(f"    [{m.role}] {m.content[:100]}...")

    print(f"\n  {'─' * 66}")
    print("  HYBRID MEMORY:")
    for m in hybrid.get_context()[:2]:
        print(f"    [{m.role}] {m.content[:100]}...")

    # Key insights
    print(f"\n\n  {'=' * 66}")
    print("  💡 KEY TAKEAWAYS")
    print(f"  {'=' * 66}")
    print("  • Sliding Window: Lost the first 14 messages (PAN, app ID, escalation)")
    print("  • Summary: Compressed but retained key topics (credit, KYC, UPI)")
    print("  • Hybrid: Recent detail + compressed history — best for production")
    print()
    print("  In production:")
    print("  • Use Hybrid for customer-facing agents (bounded cost, retains context)")
    print("  • Add vector store for long-term memory across sessions")
    print("  • Summary compression should use a cheap LLM (GPT-3.5, Haiku)")
    print("  • Token budget = direct cost control (each message in context = $$$)")
