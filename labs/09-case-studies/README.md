# Lab 09: Production Case Studies

> Real architectures at scale — support agents, code review bots, data pipelines, document processing.

## Labs

| Lab | System | Scale |
|-----|--------|-------|
| 9.1 | Customer Support Agent | 100K conversations/day |
| 9.2 | Code Review Agent | Multi-repo, CI-integrated |
| 9.3 | Data Pipeline Agent | Self-healing ETL, 1M events/day |
| 9.4 | Document Processing | KYC/invoice parsing, 50K docs/day |

## Prerequisites

```bash
# No external dependencies — architecture simulations
```

## Quick Start

```bash
cd labs/09-case-studies
python lab_1_support_agent.py        # Full support agent architecture
python lab_2_code_review.py          # CI-integrated code review
python lab_3_data_pipeline.py        # Self-healing ETL agent
python lab_4_document_processing.py  # KYC document parsing at scale
```

## Key Principle

Every case study follows the same pattern:
1. **Design** for the happy path
2. **Instrument** everything from day 1
3. **Handle** the failure modes specific to your domain
4. **Scale** based on actual bottlenecks, not guesses
