"""MAP-Elites Quality-Diversity archive."""

from __future__ import annotations

import random
from typing import Any, Callable

from algorithm_discovery_lab.core.candidate import Candidate, CandidateState
from algorithm_discovery_lab.core.problem import DiscoveryProblem
from algorithm_discovery_lab.search.base import SearchStrategy, SearchResult
from algorithm_discovery_lab.search.events import EventType, SearchEvent
from algorithm_discovery_lab.verification.verifier import get_verifier


class MAPElitesArchive:
    """Grid-based Quality-Diversity archive."""

    def __init__(
        self,
        descriptor_bins: dict[str, tuple[float, float, int]],
    ) -> None:
        self.descriptor_bins = descriptor_bins
        self.grid: dict[tuple[int, ...], tuple[float, dict[str, float], Candidate]] = {}
        self._axis_names = list(descriptor_bins.keys())

    def _discretize(self, descriptor: dict[str, float]) -> tuple[int, ...]:
        bins = []
        for name in self._axis_names:
            low, high, num_bins = self.descriptor_bins[name]
            val = descriptor.get(name, low)
            val = max(low, min(high, val))
            idx = int((val - low) / (high - low + 1e-9) * num_bins)
            idx = min(idx, num_bins - 1)
            bins.append(idx)
        return tuple(bins)

    def _objective_key(self, metrics: dict[str, float]) -> float:
        """Primary objective for comparison (lower is better)."""
        return metrics.get("comparator_count", float("inf"))

    def add(
        self, candidate: Candidate, metrics: dict[str, float], descriptor: dict[str, float]
    ) -> bool:
        key = self._discretize(descriptor)
        if key in self.grid:
            existing_key = self._objective_key(self.grid[key][1])
            new_key = self._objective_key(metrics)
            if new_key >= existing_key:
                return False
        self.grid[key] = (self._objective_key(metrics), metrics, candidate)
        return True

    @property
    def coverage(self) -> float:
        total = 1
        for _, _, n in self.descriptor_bins.values():
            total *= n
        return len(self.grid) / total if total > 0 else 0.0

    @property
    def best_solutions(self) -> list[tuple[dict[str, float], Candidate]]:
        return [(m, c) for _, m, c in self.grid.values()]

    def get_grid_data(self) -> list[dict[str, Any]]:
        result = []
        for key, (obj, metrics, candidate) in self.grid.items():
            result.append({
                "key": list(key),
                "metrics": metrics,
                "candidate_id": candidate.id,
                "objective": obj,
            })
        return result


class MAPElitesSearch(SearchStrategy):
    """MAP-Elites quality-diversity search."""

    def search(
        self,
        problem: DiscoveryProblem,
        config: dict[str, Any],
        seed: int,
        callback: Callable[[SearchEvent], None] | None = None,
    ) -> SearchResult:
        rng = random.Random(seed)
        pop_size = config.get("population_size", 200)
        generations = config.get("generations", 500)
        mutation_rate = config.get("mutation_rate", 0.3)
        n = config.get("n", 8)

        max_comp = n * (n - 1) // 2
        archive = MAPElitesArchive({
            "comparator_count": (1.0, float(max_comp), min(max_comp, 20)),
            "depth": (1.0, float(n * 2), min(n * 2, 20)),
        })

        verifier = get_verifier(config.get("verification_backend", "exhaustive"), n)
        result = SearchResult()

        # Initialize archive with random candidates
        for _ in range(pop_size * 2):
            net = problem.generate_random_candidate(rng)
            if not problem.is_valid(net):
                continue
            vr = verifier.verify(net)
            if not vr.verified:
                continue
            metrics = problem.fitness(net)
            descriptor = {
                "comparator_count": metrics["comparator_count"],
                "depth": metrics["depth"],
            }
            c = Candidate(
                problem_type=problem.__class__.__name__,
                representation=problem.serialize(net),
                state=CandidateState.VERIFIED,
                verification=vr,
                cost_metrics=metrics,
                seed=seed,
            )
            archive.add(c, metrics, descriptor)
            result.verified_candidates.append(c)
            result.total_evaluated += 1
            result.total_verified += 1

        event = SearchEvent(
            event_type=EventType.GENERATION_COMPLETED,
            generation=0,
            data={"archive_size": len(archive.grid), "coverage": archive.coverage},
        )
        result.events.append(event)
        if callback:
            callback(event)

        for gen in range(generations):
            gen_verified = 0
            for _ in range(pop_size):
                # Select random elite from archive
                if not archive.grid:
                    net = problem.generate_random_candidate(rng)
                else:
                    key = rng.choice(list(archive.grid.keys()))
                    parent_candidate = archive.grid[key][2]
                    parent_net = problem.deserialize(parent_candidate.representation)
                    net = problem.mutate(parent_net, rng)

                if not problem.is_valid(net):
                    continue

                vr = verifier.verify(net)
                result.total_evaluated += 1
                if not vr.verified:
                    continue

                gen_verified += 1
                result.total_verified += 1
                metrics = problem.fitness(net)
                descriptor = {
                    "comparator_count": metrics["comparator_count"],
                    "depth": metrics["depth"],
                }
                c = Candidate(
                    problem_type=problem.__class__.__name__,
                    representation=problem.serialize(net),
                    state=CandidateState.VERIFIED,
                    verification=vr,
                    cost_metrics=metrics,
                    generation=gen,
                    seed=seed,
                )
                added = archive.add(c, metrics, descriptor)
                if added:
                    result.verified_candidates.append(c)
                    event = SearchEvent(
                        event_type=EventType.ARCHIVE_UPDATED,
                        generation=gen,
                        candidate_id=c.id,
                        data={
                            "archive_size": len(archive.grid),
                            "coverage": archive.coverage,
                            "comparator_count": metrics["comparator_count"],
                            "depth": metrics["depth"],
                        },
                    )
                    result.events.append(event)
                    if callback:
                        callback(event)

            if gen % 10 == 0:
                event = SearchEvent(
                    event_type=EventType.GENERATION_COMPLETED,
                    generation=gen,
                    data={
                        "archive_size": len(archive.grid),
                        "coverage": archive.coverage,
                        "verified_this_gen": gen_verified,
                    },
                )
                result.events.append(event)
                if callback:
                    callback(event)

        # Pick best from archive
        if archive.grid:
            best_obj, best_metrics, best_c = min(archive.grid.values(), key=lambda x: x[0])
            result.best_candidate = best_c

        result.generations_run = generations
        result.data = {"archive": archive}  # type: ignore
        return result
