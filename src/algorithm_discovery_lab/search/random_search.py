"""Random search strategy - baseline for comparison."""

from __future__ import annotations

import random
from typing import Any, Callable

from algorithm_discovery_lab.core.candidate import Candidate, CandidateState, VerificationResult
from algorithm_discovery_lab.core.problem import DiscoveryProblem
from algorithm_discovery_lab.search.base import SearchStrategy, SearchResult
from algorithm_discovery_lab.search.events import EventType, SearchEvent
from algorithm_discovery_lab.verification.verifier import get_verifier


class RandomSearch(SearchStrategy):
    """Generate random candidates and verify them."""

    def search(
        self,
        problem: DiscoveryProblem,
        config: dict[str, Any],
        seed: int,
        callback: Callable[[SearchEvent], None] | None = None,
    ) -> SearchResult:
        rng = random.Random(seed)
        budget = config.get("budget", 500)
        verifier = get_verifier(config.get("verification_backend", "exhaustive"), config.get("n", 8))

        result = SearchResult()
        best = None

        for i in range(budget):
            net = problem.generate_random_candidate(rng)
            candidate = Candidate(
                problem_type=problem.__class__.__name__,
                representation=problem.serialize(net),
                state=CandidateState.GENERATED,
                generation=i,
                seed=seed,
            )
            result.all_candidates.append(candidate)
            result.total_evaluated += 1

            if not problem.is_valid(net):
                candidate.state = CandidateState.REJECTED
                continue

            vr = verifier.verify(net)
            candidate.verification = vr
            candidate.cost_metrics = problem.fitness(net)

            if vr.verified:
                candidate.state = CandidateState.VERIFIED
                result.verified_candidates.append(candidate)
                result.total_verified += 1

                if best is None or candidate.cost_metrics.get("comparator_count", float("inf")) < best.cost_metrics.get("comparator_count", float("inf")):
                    best = candidate
                    event = SearchEvent(
                        event_type=EventType.NEW_BEST_FOUND,
                        generation=i,
                        candidate_id=candidate.id,
                        data={
                            "comparator_count": candidate.cost_metrics["comparator_count"],
                            "depth": candidate.cost_metrics["depth"],
                        },
                    )
                    result.events.append(event)
                    if callback:
                        callback(event)
            else:
                candidate.state = CandidateState.REJECTED

            if i % 50 == 0:
                event = SearchEvent(
                    event_type=EventType.GENERATION_COMPLETED,
                    generation=i,
                    data={"verified": len(result.verified_candidates)},
                )
                result.events.append(event)
                if callback:
                    callback(event)

        result.best_candidate = best
        result.generations_run = budget
        return result
