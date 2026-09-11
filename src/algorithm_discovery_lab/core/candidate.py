"""Core data models for candidates, discoveries, and problems."""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class CandidateState(enum.Enum):
    GENERATED = "generated"
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    BENCHMARKED = "benchmarked"
    REPRODUCED = "reproduced"
    ARCHIVED = "archived"
    REJECTED = "rejected"


@dataclass
class VerificationResult:
    verified: bool
    method: str
    inputs_tested: int
    failures: list[list[int]] = field(default_factory=list)
    counterexample: list[int] | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "method": self.method,
            "inputs_tested": self.inputs_tested,
            "failures": self.failures,
            "counterexample": self.counterexample,
            "duration_ms": self.duration_ms,
        }


@dataclass
class BenchmarkResult:
    candidate_id: str
    runs: int
    median_ns: float
    mean_ns: float
    stddev_ns: float
    min_ns: float
    max_ns: float
    comparator_count: int = 0
    depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "runs": self.runs,
            "median_ns": self.median_ns,
            "mean_ns": self.mean_ns,
            "stddev_ns": self.stddev_ns,
            "min_ns": self.min_ns,
            "max_ns": self.max_ns,
            "comparator_count": self.comparator_count,
            "depth": self.depth,
        }


@dataclass
class Candidate:
    """A candidate algorithm implementation."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    problem_type: str = ""
    representation: Any = None
    state: CandidateState = CandidateState.GENERATED
    cost_metrics: dict[str, float] = field(default_factory=dict)
    verification: VerificationResult | None = None
    benchmark: BenchmarkResult | None = None
    parent_ids: list[str] = field(default_factory=list)
    generation: int = 0
    seed: int = 0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "problem_type": self.problem_type,
            "state": self.state.value,
            "cost_metrics": self.cost_metrics,
            "verification": self.verification.to_dict() if self.verification else None,
            "benchmark": self.benchmark.to_dict() if self.benchmark else None,
            "parent_ids": self.parent_ids,
            "generation": self.generation,
            "seed": self.seed,
            "created_at": self.created_at,
        }
