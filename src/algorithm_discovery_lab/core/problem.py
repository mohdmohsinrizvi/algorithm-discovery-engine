"""Problem definition interfaces."""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ProblemType(enum.Enum):
    SORTING_NETWORK = "sorting_network"
    BIT_MANIPULATION = "bit_manipulation"
    HASH_MIXER = "hash_mixer"
    MIN_MAX_NETWORK = "min_max_network"


@dataclass
class ProblemConfig:
    problem_type: ProblemType
    params: dict[str, Any] = field(default_factory=dict)
    search_config: dict[str, Any] = field(default_factory=dict)
    seed: int = 42


class DiscoveryProblem(ABC):
    """Abstract interface for discovery problems."""

    @abstractmethod
    def generate_random_candidate(self, rng: Any) -> Any:
        """Generate a random candidate solution."""

    @abstractmethod
    def mutate(self, candidate: Any, rng: Any) -> Any:
        """Mutate a candidate."""

    @abstractmethod
    def crossover(self, parent1: Any, parent2: Any, rng: Any) -> Any:
        """Crossover two candidates."""

    @abstractmethod
    def fitness(self, candidate: Any) -> dict[str, float]:
        """Compute cost metrics for a candidate."""

    @abstractmethod
    def is_valid(self, candidate: Any) -> bool:
        """Check structural validity."""

    @abstractmethod
    def get_baseline(self) -> Any:
        """Return baseline candidate."""

    @abstractmethod
    def serialize(self, candidate: Any) -> Any:
        """Serialize candidate for storage."""

    @abstractmethod
    def deserialize(self, data: Any) -> Any:
        """Deserialize candidate from storage."""

    @abstractmethod
    def display(self, candidate: Any) -> str:
        """Human-readable display of candidate."""
