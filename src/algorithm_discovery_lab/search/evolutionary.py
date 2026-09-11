"""Evolutionary search strategy."""

from __future__ import annotations

import random
from typing import Any, Callable

from algorithm_discovery_lab.core.candidate import Candidate, CandidateState
from algorithm_discovery_lab.core.problem import DiscoveryProblem
from algorithm_discovery_lab.search.base import SearchStrategy, SearchResult
from algorithm_discovery_lab.search.events import EventType, SearchEvent
from algorithm_discovery_lab.verification.verifier import get_verifier


def _pareto_dominates(a: dict[str, float], b: dict[str, float]) -> bool:
    """Check if a Pareto-dominates b (minimization)."""
    dominated = False
    for key in a:
        if key not in b:
            continue
        if a[key] > b[key]:
            return False
        if a[key] < b[key]:
            dominated = True
    return dominated


class EvolutionarySearch(SearchStrategy):
    """Multi-objective evolutionary search with tournament selection."""

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
        mutation_rate = config.get("mutation_rate", 0.15)
        crossover_rate = config.get("crossover_rate", 0.7)
        elitism_rate = config.get("elitism_rate", 0.05)
        tournament_size = config.get("tournament_size", 3)
        n = config.get("n", 8)

        verifier = get_verifier(config.get("verification_backend", "exhaustive"), n)
        result = SearchResult()

        # Initialize population: mix baseline variants + random
        population: list[tuple[Any, dict[str, float], Candidate]] = []
        baseline = problem.get_baseline()

        # Add baseline and its mutated variants
        half = pop_size // 2
        for i in range(half):
            if i == 0:
                net = baseline
            else:
                net = problem.mutate(baseline, rng)
            if not problem.is_valid(net):
                continue
            metrics = problem.fitness(net)
            c = Candidate(
                problem_type=problem.__class__.__name__,
                representation=problem.serialize(net),
                state=CandidateState.GENERATED,
                seed=seed,
            )
            population.append((net, metrics, c))

        # Fill rest with random candidates
        for _ in range(pop_size - len(population)):
            net = problem.generate_random_candidate(rng)
            if not problem.is_valid(net):
                continue
            metrics = problem.fitness(net)
            c = Candidate(
                problem_type=problem.__class__.__name__,
                representation=problem.serialize(net),
                state=CandidateState.GENERATED,
                seed=seed,
            )
            population.append((net, metrics, c))
            population.append((net, metrics, c))

        if not population:
            return result

        best_candidate = None
        verified_archive: list[Candidate] = []

        for gen in range(generations):
            # Verify top candidates each generation
            verified_this_gen = 0
            for net, metrics, candidate in population:
                if candidate.state == CandidateState.VERIFIED:
                    continue
                vr = verifier.verify(net)
                candidate.verification = vr
                candidate.cost_metrics = metrics
                candidate.generation = gen
                if vr.verified:
                    candidate.state = CandidateState.VERIFIED
                    verified_this_gen += 1
                    verified_archive.append(candidate)
                    if best_candidate is None or _pareto_dominates(metrics, best_candidate.cost_metrics):
                        best_candidate = candidate
                        event = SearchEvent(
                            event_type=EventType.NEW_BEST_FOUND,
                            generation=gen,
                            candidate_id=candidate.id,
                            data={
                                "comparator_count": metrics["comparator_count"],
                                "depth": metrics["depth"],
                            },
                        )
                        result.events.append(event)
                        if callback:
                            callback(event)
                else:
                    candidate.state = CandidateState.REJECTED

            result.total_evaluated += len(population)
            result.total_verified += verified_this_gen

            event = SearchEvent(
                event_type=EventType.GENERATION_COMPLETED,
                generation=gen,
                data={
                    "population_size": len(population),
                    "verified_this_gen": verified_this_gen,
                    "total_verified": len(verified_archive),
                },
            )
            result.events.append(event)
            if callback:
                callback(event)

            # Selection + reproduction
            new_pop: list[tuple[Any, dict[str, float], Candidate]] = []

            # Elitism
            sorted_pop = sorted(population, key=lambda x: _objective_tuple(x[1]))
            elites = sorted_pop[: max(1, int(len(sorted_pop) * elitism_rate))]
            for net, metrics, c in elites:
                nc = Candidate(
                    problem_type=c.problem_type,
                    representation=c.representation,
                    state=c.state,
                    cost_metrics=c.cost_metrics,
                    verification=c.verification,
                    parent_ids=[c.id],
                    generation=gen + 1,
                    seed=seed,
                )
                new_pop.append((net, metrics, nc))

            # Fill rest via selection + mutation + crossover
            while len(new_pop) < pop_size:
                if rng.random() < crossover_rate and len(population) >= 2:
                    p1 = self._tournament_select(population, tournament_size, rng)
                    p2 = self._tournament_select(population, tournament_size, rng)
                    child_net = problem.crossover(p1[0], p2[0], rng)
                    parent_ids = [p1[2].id, p2[2].id]
                else:
                    parent = self._tournament_select(population, tournament_size, rng)
                    child_net = parent[0]
                    parent_ids = [parent[2].id]

                if rng.random() < mutation_rate:
                    child_net = problem.mutate(child_net, rng)

                if problem.is_valid(child_net):
                    metrics = problem.fitness(child_net)
                    nc = Candidate(
                        problem_type=problem.__class__.__name__,
                        representation=problem.serialize(child_net),
                        state=CandidateState.GENERATED,
                        parent_ids=parent_ids,
                        generation=gen + 1,
                        seed=seed,
                    )
                    new_pop.append((child_net, metrics, nc))

            population = new_pop

        result.best_candidate = best_candidate
        result.verified_candidates = verified_archive
        result.generations_run = generations
        return result

    def _tournament_select(
        self,
        population: list[tuple[Any, dict[str, float], Candidate]],
        size: int,
        rng: random.Random,
    ) -> tuple[Any, dict[str, float], Candidate]:
        candidates = rng.sample(population, min(size, len(population)))
        return min(candidates, key=lambda x: _objective_tuple(x[1]))


def _objective_tuple(metrics: dict[str, float]) -> tuple[float, ...]:
    """Lexicographic ordering: comparator_count first, then depth."""
    return (metrics.get("comparator_count", float("inf")), metrics.get("depth", float("inf")))
