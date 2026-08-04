"""Lab 8.4: Self-Hosted Inference — Deploy Models with vLLM/Ollama

Run LLMs locally or on your own infrastructure for:
- Data privacy (nothing leaves your network)
- Cost control (no per-token billing)
- Low latency (no network hop to API provider)
- Custom models (fine-tuned, distilled)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    name: str
    size_gb: float
    context_length: int
    tokens_per_second: float  # Typical throughput
    min_gpu_vram_gb: int
    quantization: str = "none"  # none, fp16, int8, int4
    use_case: str = ""


@dataclass
class InferenceServer:
    name: str
    model: ModelConfig
    gpu_vram_gb: int = 24
    max_concurrent: int = 4
    active_requests: int = 0
    total_tokens: int = 0
    total_requests: int = 0
    _start_time: float = field(default_factory=time.time)

    def can_serve(self) -> bool:
        return (self.model.min_gpu_vram_gb <= self.gpu_vram_gb and
                self.active_requests < self.max_concurrent)

    def generate(self, prompt: str, max_tokens: int = 256) -> dict:
        """Simulate local inference."""
        if not self.can_serve():
            return {"error": "Server at capacity", "status": 503}

        self.active_requests += 1
        # Simulate generation time
        gen_time = max_tokens / self.model.tokens_per_second
        time.sleep(min(gen_time, 0.01))  # Scale down for demo
        self.active_requests -= 1

        self.total_tokens += max_tokens
        self.total_requests += 1

        return {
            "text": f"[{self.model.name}] Generated {max_tokens} tokens for: {prompt[:50]}...",
            "tokens": max_tokens,
            "latency_ms": round(gen_time * 1000, 1),
            "tokens_per_second": self.model.tokens_per_second,
        }

    @property
    def stats(self) -> dict:
        uptime = time.time() - self._start_time
        return {
            "model": self.model.name,
            "gpu_vram": f"{self.gpu_vram_gb}GB",
            "quantization": self.model.quantization,
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "uptime_s": round(uptime, 1),
            "avg_tps": round(self.model.tokens_per_second, 1),
        }


# --- Model Catalog ---

MODELS = {
    "llama-3.1-70b-fp16": ModelConfig(
        name="Llama 3.1 70B (FP16)", size_gb=140, context_length=128000,
        tokens_per_second=25, min_gpu_vram_gb=140, quantization="fp16",
        use_case="Maximum quality, multi-GPU clusters",
    ),
    "llama-3.1-70b-int4": ModelConfig(
        name="Llama 3.1 70B (INT4/AWQ)", size_gb=40, context_length=128000,
        tokens_per_second=45, min_gpu_vram_gb=48, quantization="int4",
        use_case="Best quality/cost balance, single A100 80GB",
    ),
    "llama-3.1-8b-int4": ModelConfig(
        name="Llama 3.1 8B (INT4)", size_gb=5, context_length=128000,
        tokens_per_second=120, min_gpu_vram_gb=8, quantization="int4",
        use_case="Fast agent tasks, function calling, RTX 4090",
    ),
    "mistral-7b-int4": ModelConfig(
        name="Mistral 7B (INT4)", size_gb=4.5, context_length=32000,
        tokens_per_second=130, min_gpu_vram_gb=8, quantization="int4",
        use_case="Coding, structured output, consumer GPUs",
    ),
    "qwen-2.5-72b-int4": ModelConfig(
        name="Qwen 2.5 72B (INT4)", size_gb=42, context_length=128000,
        tokens_per_second=40, min_gpu_vram_gb=48, quantization="int4",
        use_case="Multilingual, code, math — strong all-rounder",
    ),
}


# --- Deployment Configs ---

DEPLOYMENT_COMMANDS = {
    "vllm": """
# vLLM: High-throughput serving with PagedAttention
pip install vllm
python -m vllm.entrypoints.openai.api_server \\
    --model meta-llama/Llama-3.1-8B-Instruct \\
    --quantization awq \\
    --max-model-len 32000 \\
    --gpu-memory-utilization 0.90 \\
    --port 8000

# Key flags:
#   --tensor-parallel-size 4    (multi-GPU)
#   --enable-prefix-caching     (shared prefix = faster)
#   --max-num-seqs 256          (concurrent requests)
""",
    "ollama": """
# Ollama: Simple local inference (great for dev)
brew install ollama
ollama serve &
ollama pull llama3.1:8b-instruct-q4_K_M

# Use like OpenAI API:
curl http://localhost:11434/v1/chat/completions \\
    -d '{"model":"llama3.1:8b","messages":[{"role":"user","content":"hello"}]}'
""",
    "tgi": """
# Text Generation Inference (HuggingFace)
docker run --gpus all -p 8080:80 \\
    ghcr.io/huggingface/text-generation-inference:latest \\
    --model-id meta-llama/Llama-3.1-8B-Instruct \\
    --quantize awq \\
    --max-input-tokens 4096 \\
    --max-total-tokens 8192
""",
}


# --- Cost Calculator ---

def calculate_cost_comparison(requests_per_day: int, avg_tokens: int = 500):
    """Compare self-hosted vs API costs."""
    # API costs (per 1M tokens)
    api_costs = {
        "GPT-4o": 6.25,
        "GPT-4o-mini": 0.375,
        "Claude Sonnet": 9.0,
    }

    # Self-hosted costs (monthly)
    infra_costs = {
        "1x A100 80GB (cloud)": {"monthly": 2500, "tps": 45, "model": "70B INT4"},
        "1x RTX 4090 (own)": {"monthly": 150, "tps": 120, "model": "8B INT4"},  # Electricity only
        "4x A100 cluster": {"monthly": 10000, "tps": 200, "model": "70B FP16"},
    }

    daily_tokens = requests_per_day * avg_tokens
    monthly_tokens = daily_tokens * 30

    results = {"api": {}, "self_hosted": {}}

    for name, cost_per_m in api_costs.items():
        monthly_cost = monthly_tokens / 1_000_000 * cost_per_m
        results["api"][name] = round(monthly_cost, 2)

    for name, info in infra_costs.items():
        max_monthly_tokens = info["tps"] * 86400 * 30  # Max throughput
        utilization = min(1.0, monthly_tokens / max_monthly_tokens)
        results["self_hosted"][name] = {
            "monthly": info["monthly"],
            "utilization": round(utilization * 100, 1),
            "model": info["model"],
        }

    return results


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 8.4: Self-Hosted Inference")
    print("  Deploy models locally with vLLM, Ollama, or TGI")
    print("=" * 70)
    print()

    # Model selection guide
    print("  MODEL SELECTION GUIDE:")
    print(f"  {'Model':<30} {'VRAM':<8} {'TPS':<6} {'Context':<9} {'Use Case'}")
    print(f"  {'─'*30} {'─'*8} {'─'*6} {'─'*9} {'─'*35}")
    for key, m in MODELS.items():
        print(f"  {m.name:<30} {m.min_gpu_vram_gb:<6}GB {m.tokens_per_second:<6.0f} {m.context_length//1000:<7}K {m.use_case[:35]}")

    # Simulate serving
    print(f"\n  {'─' * 66}")
    print("  SERVING SIMULATION (Llama 3.1 8B on RTX 4090):")
    server = InferenceServer(
        name="local-llama",
        model=MODELS["llama-3.1-8b-int4"],
        gpu_vram_gb=24,
        max_concurrent=8,
    )

    prompts = [
        "Classify this transaction as fraud or legitimate",
        "Extract PAN number from this document",
        "Summarize this customer complaint",
        "Generate SQL query for credit report",
        "Score this loan application",
    ]

    for prompt in prompts:
        result = server.generate(prompt, max_tokens=200)
        print(f"    {prompt[:45]:<48} → {result['latency_ms']:>6.0f}ms ({result['tokens_per_second']} tps)")

    print(f"\n  Server stats: {server.stats}")

    # Cost comparison
    print(f"\n  {'─' * 66}")
    print("  COST COMPARISON (10,000 requests/day, 500 tokens avg):")
    costs = calculate_cost_comparison(10000, 500)
    print(f"\n    API costs (monthly):")
    for name, cost in costs["api"].items():
        print(f"      {name:<20}: ${cost:>8.2f}")
    print(f"\n    Self-hosted (monthly):")
    for name, info in costs["self_hosted"].items():
        print(f"      {name:<25}: ${info['monthly']:>6} ({info['model']}, {info['utilization']}% utilized)")

    print(f"\n  {'─' * 66}")
    print("  💡 WHEN TO SELF-HOST:")
    print("    ✅ Data can't leave your network (healthcare, finance, defense)")
    print("    ✅ High volume (>50K requests/day makes self-hosting cheaper)")
    print("    ✅ Need custom/fine-tuned models")
    print("    ✅ Latency-sensitive (no network hop)")
    print("    ❌ Low volume (<1K req/day) — APIs are cheaper")
    print("    ❌ Need frontier intelligence (GPT-4o, Claude Sonnet)")
    print("    ❌ Don't want to manage infrastructure")
