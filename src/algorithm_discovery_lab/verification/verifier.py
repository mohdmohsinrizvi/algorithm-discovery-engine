"""Verification engine with pluggable backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import product
import time

from algorithm_discovery_lab.core.candidate import VerificationResult
from algorithm_discovery_lab.problems.sorting_network import SortingNetwork


class Verifier(ABC):
    """Abstract base verifier."""

    @abstractmethod
    def verify(self, network: SortingNetwork) -> VerificationResult:
        """Verify a sorting network."""


class ExhaustiveVerifier(Verifier):
    """Exhaustively test all binary inputs for sorting network correctness."""

    def verify(self, network: SortingNetwork) -> VerificationResult:
        start = time.perf_counter()
        n = network.n
        inputs_tested = 0
        failures: list[list[int]] = []

        for bits in product(range(2), repeat=n):
            inp = list(bits)
            expected = sorted(inp)
            result = network.apply(inp)
            inputs_tested += 1
            if result != expected:
                failures.append(inp)
                if len(failures) >= 10:
                    break

        elapsed_ms = (time.perf_counter() - start) * 1000

        return VerificationResult(
            verified=len(failures) == 0,
            method="exhaustive_binary_input_verification",
            inputs_tested=inputs_tested,
            failures=failures,
            counterexample=failures[0] if failures else None,
            duration_ms=elapsed_ms,
        )


class ExhaustiveIntVerifier(Verifier):
    """Exhaustively test all permutations of [0..n-1] for sorting correctness."""

    def verify(self, network: SortingNetwork) -> VerificationResult:
        start = time.perf_counter()
        n = network.n
        inputs_tested = 0
        failures: list[list[int]] = []

        for perm in product(range(n), repeat=n):
            inp = list(perm)
            expected = sorted(inp)
            result = network.apply(inp)
            inputs_tested += 1
            if result != expected:
                failures.append(inp)
                if len(failures) >= 10:
                    break

        elapsed_ms = (time.perf_counter() - start) * 1000

        return VerificationResult(
            verified=len(failures) == 0,
            method="exhaustive_int_input_verification",
            inputs_tested=inputs_tested,
            failures=failures,
            counterexample=failures[0] if failures else None,
            duration_ms=elapsed_ms,
        )


def get_verifier(backend: str = "exhaustive", n: int = 8) -> Verifier:
    """Factory for verifier backends."""
    if backend == "exhaustive":
        if n <= 8:
            return ExhaustiveVerifier()
        return ExhaustiveIntVerifier()
    raise ValueError(f"Unknown verifier backend: {backend}")
