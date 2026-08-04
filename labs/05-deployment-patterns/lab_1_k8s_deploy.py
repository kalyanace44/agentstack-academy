"""Lab 5.1: Kubernetes Deployment for AI Agents

Generate and understand production K8s manifests for deploying AI agents:
- Deployment with resource limits (prevent OOM from large contexts)
- HPA scaling on custom metrics (queue depth, request latency)
- Service + Ingress for API access
- ConfigMap/Secrets for model config and API keys
- PodDisruptionBudget for zero-downtime updates

This lab generates the manifests and explains each decision.
"""
from __future__ import annotations

import json
import yaml
from dataclasses import dataclass


@dataclass
class AgentDeployConfig:
    """Configuration for deploying an AI agent to K8s."""
    name: str
    image: str
    replicas: int = 3
    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    memory_request: str = "512Mi"
    memory_limit: str = "2Gi"
    port: int = 8000
    # Scaling
    min_replicas: int = 2
    max_replicas: int = 20
    target_cpu_percent: int = 70
    # Agent-specific
    model_provider: str = "openai"
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    # Health
    health_path: str = "/health"
    ready_path: str = "/ready"
    startup_seconds: int = 30


def generate_deployment(cfg: AgentDeployConfig) -> dict:
    """Generate K8s Deployment manifest."""
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": cfg.name,
            "labels": {"app": cfg.name, "component": "agent"},
        },
        "spec": {
            "replicas": cfg.replicas,
            "selector": {"matchLabels": {"app": cfg.name}},
            "strategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxUnavailable": 0, "maxSurge": 1},
            },
            "template": {
                "metadata": {
                    "labels": {"app": cfg.name, "component": "agent"},
                    "annotations": {
                        "prometheus.io/scrape": "true",
                        "prometheus.io/port": str(cfg.port),
                    },
                },
                "spec": {
                    "serviceAccountName": f"{cfg.name}-sa",
                    "containers": [{
                        "name": cfg.name,
                        "image": cfg.image,
                        "ports": [{"containerPort": cfg.port, "name": "http"}],
                        "env": [
                            {"name": "PORT", "value": str(cfg.port)},
                            {"name": "MAX_CONCURRENT", "value": str(cfg.max_concurrent_tasks)},
                            {"name": "TASK_TIMEOUT", "value": str(cfg.task_timeout_seconds)},
                            {"name": "MODEL_PROVIDER", "valueFrom": {
                                "configMapKeyRef": {"name": f"{cfg.name}-config", "key": "model_provider"},
                            }},
                            {"name": "API_KEY", "valueFrom": {
                                "secretKeyRef": {"name": f"{cfg.name}-secrets", "key": "api_key"},
                            }},
                        ],
                        "resources": {
                            "requests": {"cpu": cfg.cpu_request, "memory": cfg.memory_request},
                            "limits": {"cpu": cfg.cpu_limit, "memory": cfg.memory_limit},
                        },
                        "livenessProbe": {
                            "httpGet": {"path": cfg.health_path, "port": cfg.port},
                            "initialDelaySeconds": 10,
                            "periodSeconds": 15,
                            "failureThreshold": 3,
                        },
                        "readinessProbe": {
                            "httpGet": {"path": cfg.ready_path, "port": cfg.port},
                            "initialDelaySeconds": 5,
                            "periodSeconds": 5,
                            "failureThreshold": 2,
                        },
                        "startupProbe": {
                            "httpGet": {"path": cfg.health_path, "port": cfg.port},
                            "initialDelaySeconds": 5,
                            "periodSeconds": 5,
                            "failureThreshold": cfg.startup_seconds // 5,
                        },
                    }],
                    "topologySpreadConstraints": [{
                        "maxSkew": 1,
                        "topologyKey": "kubernetes.io/hostname",
                        "whenUnsatisfiable": "DoNotSchedule",
                        "labelSelector": {"matchLabels": {"app": cfg.name}},
                    }],
                },
            },
        },
    }


def generate_hpa(cfg: AgentDeployConfig) -> dict:
    """Generate HPA with CPU + custom metrics."""
    return {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {"name": f"{cfg.name}-hpa"},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "name": cfg.name,
            },
            "minReplicas": cfg.min_replicas,
            "maxReplicas": cfg.max_replicas,
            "metrics": [
                {
                    "type": "Resource",
                    "resource": {"name": "cpu", "target": {"type": "Utilization", "averageUtilization": cfg.target_cpu_percent}},
                },
                {
                    "type": "Pods",
                    "pods": {
                        "metric": {"name": "agent_active_tasks"},
                        "target": {"type": "AverageValue", "averageValue": str(cfg.max_concurrent_tasks * 80 // 100)},
                    },
                },
            ],
            "behavior": {
                "scaleUp": {"stabilizationWindowSeconds": 30, "policies": [{"type": "Pods", "value": 3, "periodSeconds": 60}]},
                "scaleDown": {"stabilizationWindowSeconds": 300, "policies": [{"type": "Pods", "value": 1, "periodSeconds": 60}]},
            },
        },
    }


def generate_pdb(cfg: AgentDeployConfig) -> dict:
    """Generate PodDisruptionBudget."""
    return {
        "apiVersion": "policy/v1",
        "kind": "PodDisruptionBudget",
        "metadata": {"name": f"{cfg.name}-pdb"},
        "spec": {
            "minAvailable": max(1, cfg.min_replicas - 1),
            "selector": {"matchLabels": {"app": cfg.name}},
        },
    }


def generate_service(cfg: AgentDeployConfig) -> dict:
    """Generate Service."""
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": cfg.name, "labels": {"app": cfg.name}},
        "spec": {
            "selector": {"app": cfg.name},
            "ports": [{"port": 80, "targetPort": cfg.port, "protocol": "TCP", "name": "http"}],
            "type": "ClusterIP",
        },
    }


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 5.1: Kubernetes Deployment for AI Agents")
    print("  Generate production-ready K8s manifests")
    print("=" * 70)
    print()

    config = AgentDeployConfig(
        name="credit-scoring-agent",
        image="registry.internal/agents/credit-scoring:v1.2.0",
        replicas=3,
        cpu_request="1000m",
        cpu_limit="4000m",
        memory_request="1Gi",
        memory_limit="4Gi",
        min_replicas=3,
        max_replicas=20,
        max_concurrent_tasks=5,
        task_timeout_seconds=120,
        model_provider="openai",
    )

    manifests = {
        "Deployment": generate_deployment(config),
        "HPA": generate_hpa(config),
        "PDB": generate_pdb(config),
        "Service": generate_service(config),
    }

    for name, manifest in manifests.items():
        print(f"  {'─' * 66}")
        print(f"  {name}")
        print(f"  {'─' * 66}")
        print(yaml.dump(manifest, default_flow_style=False, indent=2)[:600])
        print(f"  ... (full manifest available)\n")

    # Explain key decisions
    print(f"\n{'=' * 70}")
    print("  KEY DEPLOYMENT DECISIONS (Why these settings matter)")
    print(f"{'=' * 70}")
    decisions = [
        ("maxUnavailable: 0", "Never reduce capacity during deploys — AI latency spikes lose customers"),
        ("topologySpreadConstraints", "Spread across nodes — one node failure won't kill all agents"),
        ("startupProbe", "LLM SDK init takes 10-30s (loading tokenizers, warming connections)"),
        ("memory limit: 4Gi", "Large contexts (32K tokens) + response buffering need RAM headroom"),
        ("HPA custom metric: active_tasks", "CPU doesn't reflect agent load — waiting on LLM is I/O, not CPU"),
        ("scaleDown stabilization: 300s", "Slow scale-down prevents thrashing during bursty traffic"),
        ("PDB minAvailable", "K8s node drain won't kill your service — critical for spot instances"),
    ]
    for setting, reason in decisions:
        print(f"  • {setting}")
        print(f"    → {reason}")
        print()

    # Write full manifests
    output_path = "/tmp/agent-k8s-manifests.yaml"
    with open(output_path, "w") as f:
        for manifest in manifests.values():
            f.write(yaml.dump(manifest, default_flow_style=False))
            f.write("---\n")
    print(f"  📄 Full manifests written to: {output_path}")
    print(f"  Apply with: kubectl apply -f {output_path}")
