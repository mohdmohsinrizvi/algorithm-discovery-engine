"""Search engine interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from algorithm_discovery_lab.core.candidate import Candidate
from algorithm_discovery_lab.core.problem import DiscoveryProblem
from algorithm_discovery_lab.search.events import SearchEvent


@dataclass
class SearchResult:
    best_candidate: Candidate | None = None
    verified_candidates: list[Candidate] = field(default_factory=list)
    all_candidates: list[Candidate] = field(default_factory=list)
    events: list[SearchEvent] = field(default_factory=list)
    generations_run: int = 0
    total_evaluated: int = 0
    total_verified: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_candidate": self.best_candidate.to_dict() if self.best_candidate else None,
            "verified_count": len(self.verified_candidates),
            "total_evaluated": self.total_evaluated,
            "total_verified": self.total_verified,
            "generations_run": self.generations_run,
        }


class SearchStrategy(ABC):
    """Abstract search strategy interface."""

    @abstractmethod
    def search(
        self,
        problem: DiscoveryProblem,
        config: dict[str, Any],
        seed: int,
        callback: Any | None = None,
    ) -> SearchResult:
        """Execute search and return results."""
