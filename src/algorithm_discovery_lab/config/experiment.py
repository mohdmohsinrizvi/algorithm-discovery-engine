"""Configuration management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class SearchConfig:
    algorithm: str = "evolutionary"
    population_size: int = 200
    generations: int = 500
    mutation_rate: float = 0.15
    crossover_rate: float = 0.7
    elitism_rate: float = 0.05
    tournament_size: int = 3
    diversity_pressure: float = 0.1


@dataclass
class ExperimentConfig:
    problem_type: str = "sorting_network"
    n: int = 8
    search: SearchConfig = field(default_factory=SearchConfig)
    objectives: list[str] = field(default_factory=lambda: ["comparator_count", "depth"])
    verification_backend: str = "exhaustive"
    benchmark_enabled: bool = True
    benchmark_repetitions: int = 1000
    seed: int = 42
    mode: str = "research"

    @classmethod
    def from_yaml(cls, path: str) -> ExperimentConfig:
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> ExperimentConfig:
        search_data = data.get("search", {})
        search = SearchConfig(**search_data) if search_data else SearchConfig()
        return cls(
            problem_type=data.get("problem", {}).get("type", data.get("problem_type", "sorting_network")),
            n=data.get("problem", {}).get("n", data.get("n", 8)),
            search=search,
            objectives=data.get("objectives", ["comparator_count", "depth"]),
            verification_backend=data.get("verification", {}).get("backend", "exhaustive"),
            benchmark_enabled=data.get("benchmark", {}).get("enabled", True),
            benchmark_repetitions=data.get("benchmark", {}).get("repetitions", 1000),
            seed=data.get("seed", 42),
            mode=data.get("mode", "research"),
        )

    def to_yaml(self, path: str) -> None:
        data = {
            "problem": {"type": self.problem_type, "n": self.n},
            "search": {
                "algorithm": self.search.algorithm,
                "population_size": self.search.population_size,
                "generations": self.search.generations,
                "mutation_rate": self.search.mutation_rate,
                "crossover_rate": self.search.crossover_rate,
                "elitism_rate": self.search.elitism_rate,
                "tournament_size": self.search.tournament_size,
                "diversity_pressure": self.search.diversity_pressure,
            },
            "objectives": self.objectives,
            "verification": {"backend": self.verification_backend},
            "benchmark": {
                "enabled": self.benchmark_enabled,
                "repetitions": self.benchmark_repetitions,
            },
            "seed": self.seed,
            "mode": self.mode,
        }
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
