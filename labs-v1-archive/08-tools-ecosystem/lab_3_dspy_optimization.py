"""Lab 8.3: DSPy Optimization — Programmatic Prompt Engineering

Instead of manually writing prompts, define what you want and let DSPy optimize.
Pattern: declare input/output signatures, provide examples, auto-optimize.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Example:
    inputs: dict
    outputs: dict
    score: float = 0.0


class Signature:
    """Declare what a module does (input → output) without writing the prompt."""

    def __init__(self, spec: str):
        # Parse "input1, input2 -> output1, output2"
        parts = spec.split("->")
        self.inputs = [s.strip() for s in parts[0].split(",")]
        self.outputs = [s.strip() for s in parts[1].split(",")]

    def __repr__(self):
        return f"Signature({', '.join(self.inputs)} -> {', '.join(self.outputs)})"


class Predictor:
    """Base predictor — takes inputs, produces outputs per signature."""

    def __init__(self, signature: Signature):
        self.signature = signature
        self.few_shot_examples: list[Example] = []
        self.instructions: str = ""
        self.calls = 0

    def __call__(self, **kwargs) -> dict:
        self.calls += 1
        # Simulate LLM call with few-shot examples
        return self._simulate_response(kwargs)

    def _simulate_response(self, inputs: dict) -> dict:
        """Simulated response based on simple heuristics."""
        outputs = {}
        for field in self.signature.outputs:
            if field == "risk_score":
                income = inputs.get("income", 0)
                score = inputs.get("credit_score", 700)
                risk = max(0, min(100, 100 - (income / 1000 + score / 10)))
                outputs[field] = round(risk, 1)
            elif field == "reasoning":
                outputs[field] = f"Based on {', '.join(f'{k}={v}' for k,v in inputs.items())}"
            elif field == "decision":
                risk = outputs.get("risk_score", 50)
                outputs[field] = "approve" if risk < 40 else "reject" if risk > 70 else "review"
            else:
                outputs[field] = f"generated_{field}"
        return outputs


class ChainOfThought(Predictor):
    """Predictor that adds reasoning steps before the answer."""

    def __call__(self, **kwargs) -> dict:
        result = super().__call__(**kwargs)
        result["_reasoning"] = f"Step 1: Analyze inputs. Step 2: Apply criteria. Step 3: {result.get('reasoning', 'Conclude.')}"
        return result


class BootstrapFewShot:
    """Optimizer: finds the best few-shot examples that maximize a metric."""

    def __init__(self, metric: callable, max_demos: int = 4):
        self.metric = metric
        self.max_demos = max_demos

    def compile(self, module: "DSPyModule", trainset: list[Example]) -> "DSPyModule":
        """Find optimal few-shot examples by trying combinations."""
        best_score = 0.0
        best_demos = []

        # Try random subsets of training examples as few-shot demos
        for trial in range(min(10, len(trainset))):
            # Random subset
            demos = random.sample(trainset, min(self.max_demos, len(trainset)))

            # Set demos and evaluate
            module.predictor.few_shot_examples = demos
            score = self._evaluate(module, trainset)

            if score > best_score:
                best_score = score
                best_demos = demos

        module.predictor.few_shot_examples = best_demos
        module._optimized = True
        module._optimization_score = best_score
        return module

    def _evaluate(self, module: "DSPyModule", examples: list[Example]) -> float:
        scores = []
        for ex in examples:
            prediction = module(**ex.inputs)
            score = self.metric(prediction, ex.outputs)
            scores.append(score)
        return sum(scores) / max(len(scores), 1)


class DSPyModule:
    """Base module that wraps a predictor with optimization support."""

    def __init__(self, signature_str: str):
        self.signature = Signature(signature_str)
        self.predictor = ChainOfThought(self.signature)
        self._optimized = False
        self._optimization_score = 0.0

    def __call__(self, **kwargs) -> dict:
        return self.predictor(**kwargs)


# --- Credit Risk Module ---

class CreditRiskScorer(DSPyModule):
    def __init__(self):
        super().__init__("income, credit_score, employment_years -> risk_score, decision, reasoning")


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 8.3: DSPy Optimization")
    print("  Programmatic prompt optimization — no manual prompting")
    print("=" * 70)
    print()

    # Define metric
    def accuracy_metric(prediction: dict, expected: dict) -> float:
        if prediction.get("decision") == expected.get("decision"):
            return 1.0
        return 0.0

    # Create training set
    trainset = [
        Example(inputs={"income": 150000, "credit_score": 750, "employment_years": 5},
                outputs={"decision": "approve", "risk_score": 25}),
        Example(inputs={"income": 30000, "credit_score": 580, "employment_years": 1},
                outputs={"decision": "reject", "risk_score": 80}),
        Example(inputs={"income": 80000, "credit_score": 680, "employment_years": 3},
                outputs={"decision": "review", "risk_score": 50}),
        Example(inputs={"income": 200000, "credit_score": 800, "employment_years": 10},
                outputs={"decision": "approve", "risk_score": 15}),
        Example(inputs={"income": 45000, "credit_score": 620, "employment_years": 2},
                outputs={"decision": "review", "risk_score": 55}),
        Example(inputs={"income": 25000, "credit_score": 550, "employment_years": 0},
                outputs={"decision": "reject", "risk_score": 85}),
    ]

    # Before optimization
    module = CreditRiskScorer()
    print("  BEFORE OPTIMIZATION:")
    print(f"  Signature: {module.signature}")
    print(f"  Few-shot examples: {len(module.predictor.few_shot_examples)}")
    pre_scores = [accuracy_metric(module(**ex.inputs), ex.outputs) for ex in trainset]
    print(f"  Accuracy: {sum(pre_scores)/len(pre_scores):.2%}")
    print()

    # Optimize
    print("  OPTIMIZING with BootstrapFewShot...")
    optimizer = BootstrapFewShot(metric=accuracy_metric, max_demos=3)
    optimized = optimizer.compile(module, trainset)
    print(f"  Selected {len(optimized.predictor.few_shot_examples)} few-shot demos")
    print(f"  Optimization score: {optimized._optimization_score:.2%}")
    print()

    # After optimization
    print("  AFTER OPTIMIZATION:")
    post_scores = [accuracy_metric(optimized(**ex.inputs), ex.outputs) for ex in trainset]
    print(f"  Accuracy: {sum(post_scores)/len(post_scores):.2%}")
    print()

    # Test on new examples
    print("  TEST ON NEW DATA:")
    test_cases = [
        {"income": 120000, "credit_score": 720, "employment_years": 4},
        {"income": 35000, "credit_score": 590, "employment_years": 1},
        {"income": 500000, "credit_score": 780, "employment_years": 15},
    ]
    for case in test_cases:
        result = optimized(**case)
        print(f"    Income=₹{case['income']:,} Score={case['credit_score']} Yrs={case['employment_years']} → {result['decision']} (risk: {result['risk_score']})")

    print(f"\n  {'─' * 66}")
    print("  💡 DSPy KEY IDEAS:")
    print("    • Define WHAT you want (signature), not HOW (no prompt writing)")
    print("    • Optimizer finds best few-shot examples automatically")
    print("    • Swap models without rewriting prompts")
    print("    • Compose modules: CreditScorer | FraudDetector | Recommender")
    print("    • Production: compile once, deploy optimized prompt")
