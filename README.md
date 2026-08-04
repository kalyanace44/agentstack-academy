# AgentStack Academy

> **The production AI engineering school.** Everyone teaches you to build an agent. We teach you to ship one.

## What We Teach

The complete stack for deploying, scaling, and operating AI agents in production — from architecture to observability.

## Curriculum

### Module 1: Agent Architectures (Foundation)
- ReAct pattern, tool-use agents, function calling
- Multi-agent orchestration (CrewAI, AutoGen, LangGraph)
- Agent communication patterns (pub/sub, shared state, message passing)
- When NOT to use agents (decision framework)

### Module 2: Memory & State Management
- Short-term (conversation buffer, sliding window, summary)
- Long-term (vector stores, knowledge graphs, entity memory)
- Memory architectures (MemGPT, generative agents, reflection)
- Production memory: TTL, eviction, consistency, multi-tenant isolation

### Module 3: RAG (Retrieval-Augmented Generation)
- Chunking strategies (semantic, recursive, parent-child)
- Embedding models (OpenAI, Cohere, local via sentence-transformers)
- Vector databases (Pinecone, Weaviate, Qdrant, pgvector, Chroma)
- Advanced retrieval (hybrid BM25+vector, reranking, HyDE, RAPTOR)
- RAG evaluation (faithfulness, relevance, context precision)

### Module 4: Guardrails & Safety
- Input validation (prompt injection detection, jailbreak prevention)
- Output validation (hallucination detection, format enforcement)
- PII/sensitive data scanning and redaction
- Cost guardrails (token budgets, rate limiting, circuit breakers)
- Guardrails frameworks (NeMo, Guardrails AI, Rebuff)

### Module 5: Deployment Patterns
- Kubernetes-native agent deployments
- Serverless agents (Lambda, Cloud Run, Modal)
- Edge deployment (local inference, quantized models)
- Scaling patterns (horizontal, queue-based, autoscaling)
- Multi-region and failover strategies

### Module 6: Observability & Debugging
- Tracing agent reasoning chains (LangSmith, Arize, Helicone)
- Debugging infinite loops and hallucination cascades
- Cost tracking and attribution (per-agent, per-task)
- Latency profiling (tool calls, LLM inference, retrieval)
- Alert engineering for agent failures

### Module 7: MLOps for Agents
- Model registry and versioning
- A/B testing agent configurations
- Canary deployments and rollbacks
- Continuous evaluation on production traffic
- Fine-tuning feedback loops

### Module 8: The Tools Ecosystem
- LangChain / LangGraph — orchestration
- CrewAI / AutoGen — multi-agent
- DSPy — programmatic prompting
- Semantic Kernel — enterprise integration
- vLLM / TGI — self-hosted inference
- Weights & Biases — experiment tracking

### Module 9: Production Case Studies
- Building a customer support agent (100K+ daily conversations)
- Deploying a code review agent (multi-repo, CI-integrated)
- Operating a data pipeline agent (ETL, monitoring, self-healing)
- Scaling a document processing agent (1M+ docs/day)

## Who This Is For

- **Backend/DevOps engineers** moving into AI engineering
- **ML engineers** who can build models but struggle with production deployment
- **CTOs/Architects** designing AI-native systems
- **SREs** responsible for operating agent workloads

## Tech Stack (Used in Labs)

- Python, FastAPI, Docker, Kubernetes
- OpenAI, Anthropic, local LLMs (vLLM, Ollama)
- Pinecone, pgvector, Qdrant
- Prometheus, Grafana, OpenTelemetry
- LangChain, CrewAI, DSPy

## License

Content: CC BY-NC-SA 4.0
Code examples: MIT
