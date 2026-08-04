"""Lab 3.4: RAG Evaluation — Measure Retrieval and Generation Quality

Evaluate RAG pipelines on 3 axes:
1. Context Relevance — did we retrieve the right chunks?
2. Faithfulness — is the answer grounded in the context?
3. Answer Relevance — does the answer address the question?
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class EvalCase:
    question: str
    expected_answer: str
    context_chunks: list[str]
    generated_answer: str


@dataclass
class EvalScore:
    context_relevance: float
    faithfulness: float
    answer_relevance: float
    overall: float


class RAGEvaluator:
    """Evaluate RAG pipeline quality using heuristic metrics.

    In production, use LLM-as-judge (GPT-4 scoring) or RAGAS framework.
    This lab uses keyword/overlap-based approximations for zero-dependency demo.
    """

    def evaluate(self, case: EvalCase) -> EvalScore:
        cr = self._context_relevance(case.question, case.context_chunks)
        ff = self._faithfulness(case.generated_answer, case.context_chunks)
        ar = self._answer_relevance(case.question, case.generated_answer)
        overall = (cr + ff + ar) / 3
        return EvalScore(
            context_relevance=round(cr, 3),
            faithfulness=round(ff, 3),
            answer_relevance=round(ar, 3),
            overall=round(overall, 3),
        )

    def _context_relevance(self, question: str, chunks: list[str]) -> float:
        """What fraction of retrieved chunks are relevant to the question?"""
        q_keywords = set(re.findall(r'\w{4,}', question.lower()))
        relevant = 0
        for chunk in chunks:
            chunk_words = set(re.findall(r'\w{4,}', chunk.lower()))
            overlap = len(q_keywords & chunk_words) / max(len(q_keywords), 1)
            if overlap > 0.2:
                relevant += 1
        return relevant / max(len(chunks), 1)

    def _faithfulness(self, answer: str, chunks: list[str]) -> float:
        """Are claims in the answer grounded in the context?"""
        context = " ".join(chunks).lower()
        # Extract factual claims (sentences with numbers or specifics)
        sentences = re.split(r'[.!?]+', answer)
        grounded = 0
        total_claims = 0
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            total_claims += 1
            # Check if key terms from the sentence appear in context
            sent_keywords = set(re.findall(r'\w{5,}', sent.lower()))
            context_keywords = set(re.findall(r'\w{5,}', context))
            overlap = len(sent_keywords & context_keywords)
            if overlap >= 2 or len(sent_keywords) == 0:
                grounded += 1
        return grounded / max(total_claims, 1)

    def _answer_relevance(self, question: str, answer: str) -> float:
        """Does the answer address the question?"""
        q_keywords = set(re.findall(r'\w{4,}', question.lower()))
        a_keywords = set(re.findall(r'\w{4,}', answer.lower()))
        if not q_keywords:
            return 1.0
        return min(1.0, len(q_keywords & a_keywords) / len(q_keywords))


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 3.4: RAG Evaluation")
    print("  Measure: Context Relevance, Faithfulness, Answer Relevance")
    print("=" * 70)
    print()

    evaluator = RAGEvaluator()

    cases = [
        EvalCase(
            question="How do I scale AI agents on Kubernetes?",
            expected_answer="Use HPA with custom metrics like queue depth and active tasks",
            context_chunks=[
                "Kubernetes HPA scales pods based on CPU utilization and custom metrics like queue depth.",
                "AI agents need 5GB+ RAM per pod for large context windows. Scale on active tasks not CPU.",
                "Circuit breakers prevent cascading failures in microservices.",  # irrelevant chunk
            ],
            generated_answer="To scale AI agents on Kubernetes, use HPA with custom metrics like queue depth and active tasks per pod. Standard CPU-based scaling doesn't work because agents spend most time waiting on LLM I/O. Set resource limits to 5GB RAM minimum per pod.",
        ),
        EvalCase(
            question="What causes AI agent failures?",
            expected_answer="Quality regression, infinite loops, cost explosion, cascading failures",
            context_chunks=[
                "Agents can fail via quality regression, infinite loops, cost explosion, and cascading failures.",
                "Vector databases store embeddings for similarity search.",  # irrelevant
            ],
            generated_answer="AI agents fail in four main ways: quality regression where outputs are wrong but valid, infinite loops where the agent keeps calling tools, cost explosion from token bugs, and cascading failures from provider outages.",
        ),
        EvalCase(
            question="How do I reduce LLM costs?",
            expected_answer="Use cheaper models, caching, budget limits",
            context_chunks=[
                "Python garbage collection uses reference counting.",  # completely irrelevant
                "Docker containers should use non-root users.",  # irrelevant
            ],
            generated_answer="To reduce costs, implement semantic caching for repeated queries, route simple tasks to GPT-4o-mini, and set per-team daily budgets with automatic throttling at 80% usage.",
        ),
    ]

    print(f"  {'Question':<40} {'CtxRel':>7} {'Faith':>7} {'AnsRel':>7} {'Overall':>8}")
    print(f"  {'─'*40} {'─'*7} {'─'*7} {'─'*7} {'─'*8}")

    for case in cases:
        score = evaluator.evaluate(case)
        print(f"  {case.question[:38]:<40} {score.context_relevance:>6.2f} {score.faithfulness:>6.2f} {score.answer_relevance:>6.2f} {score.overall:>7.2f}")

    # Analysis
    print(f"\n  {'─' * 66}")
    print("  ANALYSIS:")
    print()
    print("  Case 1 (Kubernetes scaling): High scores — good retrieval + grounded answer")
    print("  Case 2 (Agent failures): Good, but one irrelevant chunk hurts context relevance")
    print("  Case 3 (LLM costs): LOW context relevance — retrieved wrong chunks entirely!")
    print("         Answer is correct but NOT grounded in context = hallucination risk")
    print()
    print("  💡 KEY INSIGHT:")
    print("  • Context Relevance < 0.5 means your retrieval is broken — fix chunking/embedding")
    print("  • Faithfulness < 0.7 means the LLM is hallucinating — constrain generation")
    print("  • Answer Relevance < 0.5 means the LLM is going off-topic — improve prompt")
    print("  • In production, use RAGAS or LLM-as-judge for more accurate scoring")
