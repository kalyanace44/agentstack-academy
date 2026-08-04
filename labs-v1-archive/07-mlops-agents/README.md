# Lab 07: MLOps for Agents

> Model registry, A/B testing, canary deployments, and continuous evaluation.

## Labs

| Lab | Topic | What You Build |
|-----|-------|----------------|
| 7.1 | Model Registry | Version, tag, and promote models through stages |
| 7.2 | A/B Testing | Split traffic between agent configs, measure significance |
| 7.3 | Canary Deployments | Roll out new models gradually with auto-rollback |
| 7.4 | Continuous Eval | Detect quality regressions on production traffic |

## Prerequisites

```bash
# No external dependencies — all labs run with Python stdlib
```

## Quick Start

```bash
cd labs/07-mlops-agents
python lab_1_model_registry.py     # Version + promote models
python lab_2_ab_testing.py         # Traffic splitting + significance
python lab_3_canary.py             # Gradual rollout with rollback
python lab_4_continuous_eval.py    # Production quality monitoring
```
