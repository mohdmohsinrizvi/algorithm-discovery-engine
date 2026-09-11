"""Experiment runner - orchestrates search, verification, benchmarking, and archiving."""

from __future__ import annotations

import hashlib
import json
import platform
import time
import uuid
from typing import Any, Callable

from algorithm_discovery_lab.benchmarking.engine import benchmark_sorting_network
from algorithm_discovery_lab.config.experiment import ExperimentConfig
from algorithm_discovery_lab.core.candidate import Candidate, CandidateState
from algorithm_discovery_lab.core.discovery import Discovery
from algorithm_discovery_lab.problems.sorting_network import SortingNetwork, SortingNetworkProblem
from algorithm_discovery_lab.search.base import SearchStrategy, SearchResult
from algorithm_discovery_lab.search.events import SearchEvent
from algorithm_discovery_lab.search.evolutionary import EvolutionarySearch
from algorithm_discovery_lab.search.map_elites import MAPElitesSearch
from algorithm_discovery_lab.search.random_search import RandomSearch
from algorithm_discovery_lab.storage.db import Storage
from algorithm_discovery_lab.verification.verifier import get_verifier


def get_search_strategy(name: str) -> SearchStrategy:
    strategies = {
        "random": RandomSearch(),
        "evolutionary": EvolutionarySearch(),
        "map_elites": MAPElitesSearch(),
    }
    if name not in strategies:
        raise ValueError(f"Unknown search strategy: {name}. Available: {list(strategies.keys())}")
    return strategies[name]


def _get_hardware_info() -> dict[str, str]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "architecture": platform.machine(),
    }


class ExperimentRunner:
    """Run a complete discovery experiment."""

    def __init__(self, config: ExperimentConfig, storage: Storage | None = None) -> None:
        self.config = config
        self.storage = storage
        self.experiment_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"

    def run(
        self,
        callback: Callable[[SearchEvent], None] | None = None,
    ) -> dict[str, Any]:
        """Execute full experiment pipeline."""
        problem = SortingNetworkProblem(self.config.n)
        search = get_search_strategy(self.config.search.algorithm)

        search_config = {
            "population_size": self.config.search.population_size,
            "generations": self.config.search.generations,
            "mutation_rate": self.config.search.mutation_rate,
            "crossover_rate": self.config.search.crossover_rate,
            "elitism_rate": self.config.search.elitism_rate,
            "tournament_size": self.config.search.tournament_size,
            "n": self.config.n,
            "verification_backend": self.config.verification_backend,
        }

        if self.storage:
            self.storage.save_experiment(
                self.experiment_id, self.config.problem_type, search_config, self.config.seed
            )

        start_time = time.time()
        search_result = search.search(problem, search_config, self.config.seed, callback)
        elapsed = time.time() - start_time

        # Benchmark best candidate
        benchmark_result = {}
        if self.config.benchmark_enabled and search_result.best_candidate:
            best_net = problem.deserialize(search_result.best_candidate.representation)
            br = benchmark_sorting_network(
                best_net,
                search_result.best_candidate.id,
                repetitions=self.config.benchmark_repetitions,
            )
            search_result.best_candidate.benchmark = br
            search_result.best_candidate.state = CandidateState.BENCHMARKED
            benchmark_result = br.to_dict()

        # Save verified candidates
        if self.storage:
            for c in search_result.verified_candidates:
                self.storage.save_candidate(c, self.experiment_id)
            self.storage.complete_experiment(
                self.experiment_id,
                search_result.best_candidate.id if search_result.best_candidate else None,
            )

        # Create discovery if we found something
        discovery = None
        if search_result.best_candidate:
            best_c = search_result.best_candidate
            baseline = problem.get_baseline()
            baseline_metrics = problem.fitness(baseline)
            discovery = Discovery(
                problem=f"Sorting Network n={self.config.n}",
                domain="sorting_network",
                candidate_dict=best_c.representation,
                baseline_dict=problem.serialize(baseline),
                verification_method=best_c.verification.method if best_c.verification else "",
                verification_result=best_c.verification.to_dict() if best_c.verification else {},
                cost_metrics=best_c.cost_metrics,
                benchmark_result=benchmark_result,
                hardware=_get_hardware_info(),
                software_env={"python": platform.python_version()},
                search_config=search_config,
                search_seed=self.config.seed,
                generation_discovered=best_c.generation,
            )
            if self.storage:
                self.storage.save_discovery(discovery)

        return {
            "experiment_id": self.experiment_id,
            "config": {
                "problem": self.config.problem_type,
                "n": self.config.n,
                "search": self.config.search.algorithm,
                "seed": self.config.seed,
            },
            "result": search_result.to_dict(),
            "benchmark": benchmark_result,
            "discovery": discovery.to_dict() if discovery else None,
            "elapsed_seconds": elapsed,
            "hardware": _get_hardware_info(),
        }
