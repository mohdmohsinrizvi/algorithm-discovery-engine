"""Benchmarking engine for reproducible performance measurement."""

from __future__ import annotations

import statistics
import time
from typing import Any

from algorithm_discovery_lab.core.candidate import BenchmarkResult
from algorithm_discovery_lab.problems.sorting_network import SortingNetwork


def _median_sorting_network_time(network: SortingNetwork, arr: list[int], runs: int) -> float:
    """Measure median execution time of sorting a network on a fixed input."""
    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter_ns()
        network.apply(arr)
        end = time.perf_counter_ns()
        times.append(end - start)
    return statistics.median(times)


def benchmark_sorting_network(
    network: SortingNetwork,
    candidate_id: str,
    repetitions: int = 1000,
    warmup: int = 100,
) -> BenchmarkResult:
    """Run controlled benchmark on a sorting network."""
    import random
    rng = random.Random(0)
    n = network.n

    # Warmup
    for _ in range(warmup):
        arr = [rng.randint(0, 1000) for _ in range(n)]
        network.apply(arr)

    # Measure with fixed random inputs
    all_times: list[float] = []
    for _ in range(repetitions):
        arr = [rng.randint(0, 1000) for _ in range(n)]
        times: list[float] = []
        for _ in range(10):
            start = time.perf_counter_ns()
            network.apply(arr)
            end = time.perf_counter_ns()
            times.append(end - start)
        all_times.append(statistics.median(times))

    median_ns = statistics.median(all_times)
    mean_ns = statistics.mean(all_times)
    stddev_ns = statistics.stdev(all_times) if len(all_times) > 1 else 0.0
    min_ns = min(all_times)
    max_ns = max(all_times)

    return BenchmarkResult(
        candidate_id=candidate_id,
        runs=repetitions,
        median_ns=median_ns,
        mean_ns=mean_ns,
        stddev_ns=stddev_ns,
        min_ns=min_ns,
        max_ns=max_ns,
        comparator_count=network.comparator_count,
        depth=network.depth,
    )


def benchmark_generic(
    apply_fn: Any,
    candidate_id: str,
    input_gen: Any,
    repetitions: int = 1000,
    warmup: int = 100,
) -> BenchmarkResult:
    """Generic benchmark runner for any candidate."""
    for _ in range(warmup):
        inp = input_gen()
        apply_fn(inp)

    all_times: list[float] = []
    for _ in range(repetitions):
        inp = input_gen()
        times: list[float] = []
        for _ in range(10):
            start = time.perf_counter_ns()
            apply_fn(inp)
            end = time.perf_counter_ns()
            times.append(end - start)
        all_times.append(statistics.median(times))

    return BenchmarkResult(
        candidate_id=candidate_id,
        runs=repetitions,
        median_ns=statistics.median(all_times),
        mean_ns=statistics.mean(all_times),
        stddev_ns=statistics.stdev(all_times) if len(all_times) > 1 else 0.0,
        min_ns=min(all_times),
        max_ns=max(all_times),
    )
