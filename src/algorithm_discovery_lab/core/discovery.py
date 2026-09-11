"""Discovery record for preserving research artifacts."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Discovery:
    """A permanent research artifact capturing a verified discovery."""
    id: str = field(default_factory=lambda: f"DISC-{uuid.uuid4().hex[:8].upper()}")
    problem: str = ""
    domain: str = ""
    candidate: Any = None
    candidate_dict: dict[str, Any] = field(default_factory=dict)
    baseline: Any = None
    baseline_dict: dict[str, Any] = field(default_factory=dict)
    verification_method: str = ""
    verification_result: dict[str, Any] = field(default_factory=dict)
    cost_metrics: dict[str, float] = field(default_factory=dict)
    benchmark_result: dict[str, Any] = field(default_factory=dict)
    hardware: dict[str, str] = field(default_factory=dict)
    software_env: dict[str, str] = field(default_factory=dict)
    search_config: dict[str, Any] = field(default_factory=dict)
    search_seed: int = 0
    generation_discovered: int = 0
    parent_ids: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    commit: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "problem": self.problem,
            "domain": self.domain,
            "candidate": self.candidate_dict,
            "baseline": self.baseline_dict,
            "verification_method": self.verification_method,
            "verification_result": self.verification_result,
            "cost_metrics": self.cost_metrics,
            "benchmark_result": self.benchmark_result,
            "hardware": self.hardware,
            "software_env": self.software_env,
            "search_config": self.search_config,
            "search_seed": self.search_seed,
            "generation_discovered": self.generation_discovered,
            "parent_ids": self.parent_ids,
            "timestamp": self.timestamp,
            "commit": self.commit,
            "notes": self.notes,
        }
