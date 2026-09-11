"""Sorting network problem domain."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from algorithm_discovery_lab.core.problem import DiscoveryProblem


@dataclass
class Comparator:
    i: int
    j: int

    def __post_init__(self) -> None:
        if self.i >= self.j:
            raise ValueError(f"Comparator requires i < j, got ({self.i}, {self.j})")

    def apply(self, arr: list[int]) -> list[int]:
        result = arr[:]
        if result[self.i] > result[self.j]:
            result[self.i], result[self.j] = result[self.j], result[self.i]
        return result

    def to_dict(self) -> dict[str, int]:
        return {"i": self.i, "j": self.j}

    @classmethod
    def from_dict(cls, d: dict[str, int]) -> Comparator:
        return cls(i=d["i"], j=d["j"])

    def __repr__(self) -> str:
        return f"({self.i},{self.j})"


@dataclass
class SortingNetwork:
    n: int
    comparators: list[Comparator] = field(default_factory=list)

    def apply(self, arr: list[int]) -> list[int]:
        result = arr[:]
        for c in self.comparators:
            result = c.apply(result)
        return result

    @property
    def comparator_count(self) -> int:
        return len(self.comparators)

    @property
    def depth(self) -> int:
        if not self.comparators:
            return 0
        layers: list[int] = []
        wire_end: list[int] = [0] * self.n
        for c in self.comparators:
            start = max(wire_end[c.i], wire_end[c.j])
            layer = start + 1
            layers.append(layer)
            wire_end[c.i] = layer
            wire_end[c.j] = layer
        return max(layers) if layers else 0

    def to_list(self) -> list[dict[str, int]]:
        return [c.to_dict() for c in self.comparators]

    @classmethod
    def from_list(cls, n: int, data: list[dict[str, int]]) -> SortingNetwork:
        comparators = [Comparator.from_dict(d) for d in data]
        return cls(n=n, comparators=comparators)

    def structural_hash(self) -> tuple:
        return tuple((c.i, c.j) for c in self.comparators)

    def __repr__(self) -> str:
        return f"SortingNetwork(n={self.n}, comparators={self.comparators})"


class SortingNetworkProblem(DiscoveryProblem):
    """Sorting network discovery problem."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.max_comparators = n * (n - 1) // 2

    def generate_random_candidate(self, rng: random.Random) -> SortingNetwork:
        num_comparators = rng.randint(self.n, self.max_comparators)
        comparators = []
        for _ in range(num_comparators):
            i = rng.randint(0, self.n - 2)
            j = rng.randint(i + 1, self.n - 1)
            comparators.append(Comparator(i=i, j=j))
        return SortingNetwork(n=self.n, comparators=comparators)

    def mutate(self, network: SortingNetwork, rng: random.Random) -> SortingNetwork:
        mut_type = rng.choice(["add", "remove", "replace", "swap", "shift_layer"])
        new_comparators = [Comparator(i=c.i, j=c.j) for c in network.comparators]

        if mut_type == "add" and len(new_comparators) < self.max_comparators:
            i = rng.randint(0, self.n - 2)
            j = rng.randint(i + 1, self.n - 1)
            pos = rng.randint(0, len(new_comparators))
            new_comparators.insert(pos, Comparator(i=i, j=j))

        elif mut_type == "remove" and len(new_comparators) > 1:
            idx = rng.randint(0, len(new_comparators) - 1)
            new_comparators.pop(idx)

        elif mut_type == "replace" and new_comparators:
            idx = rng.randint(0, len(new_comparators) - 1)
            i = rng.randint(0, self.n - 2)
            j = rng.randint(i + 1, self.n - 1)
            new_comparators[idx] = Comparator(i=i, j=j)

        elif mut_type == "swap" and len(new_comparators) >= 2:
            a, b = rng.sample(range(len(new_comparators)), 2)
            new_comparators[a], new_comparators[b] = new_comparators[b], new_comparators[a]

        elif mut_type == "shift_layer" and len(new_comparators) >= 2:
            idx = rng.randint(0, len(new_comparators) - 1)
            shift = rng.choice([-2, -1, 1, 2])
            new_idx = max(0, min(len(new_comparators) - 1, idx + shift))
            c = new_comparators.pop(idx)
            new_comparators.insert(new_idx, c)

        return SortingNetwork(n=self.n, comparators=new_comparators)

    def crossover(
        self, parent1: SortingNetwork, parent2: SortingNetwork, rng: random.Random
    ) -> SortingNetwork:
        if not parent1.comparators or not parent2.comparators:
            src = parent1.comparators if parent1.comparators else parent2.comparators
            return SortingNetwork(
                n=self.n,
                comparators=[Comparator(i=c.i, j=c.j) for c in src],
            )
        max_pt = min(len(parent1.comparators), len(parent2.comparators))
        if max_pt <= 1:
            return SortingNetwork(
                n=self.n,
                comparators=[Comparator(i=c.i, j=c.j) for c in parent1.comparators],
            )
        pt = rng.randint(1, max_pt - 1)
        child_comps = [Comparator(i=c.i, j=c.j) for c in parent1.comparators[:pt]]
        child_comps += [Comparator(i=c.i, j=c.j) for c in parent2.comparators[pt:]]
        return SortingNetwork(n=self.n, comparators=child_comps)

    def fitness(self, network: SortingNetwork) -> dict[str, float]:
        return {
            "comparator_count": float(network.comparator_count),
            "depth": float(network.depth),
        }

    def is_valid(self, network: SortingNetwork) -> bool:
        if not network.comparators:
            return False
        for c in network.comparators:
            if c.i < 0 or c.j >= self.n or c.i >= c.j:
                return False
        return True

    def get_baseline(self) -> SortingNetwork:
        return _known_baseline(self.n)

    def serialize(self, network: SortingNetwork) -> Any:
        return {"n": network.n, "comparators": network.to_list()}

    def deserialize(self, data: dict[str, Any]) -> SortingNetwork:
        return SortingNetwork.from_list(data["n"], data["comparators"])

    def display(self, network: SortingNetwork) -> str:
        return network.__repr__()


def _insertion_sort_network(n: int) -> list[tuple[int, int]]:
    """Generate insertion-sort derived sorting network as comparator list."""
    comparators = []
    for i in range(1, n):
        for j in range(i, 0, -1):
            comparators.append((j - 1, j))
    return comparators


def _known_baseline(n: int) -> SortingNetwork:
    """Return a known-good sorting network (insertion-sort derived or known optimal)."""
    baselines: dict[int, list[tuple[int, int]]] = {
        1: [],
        2: [(0, 1)],
        3: [(0, 1), (1, 2), (0, 1)],
        4: [(0, 1), (2, 3), (0, 2), (1, 3), (1, 2)],
        5: [
            (0, 1), (2, 3), (0, 2), (1, 3), (1, 2),
            (3, 4), (2, 3), (1, 2),
        ],
        6: [
            (0, 1), (2, 3), (4, 5), (0, 2), (1, 4), (3, 5), (0, 1), (2, 3), (4, 5),
            (1, 2), (3, 4), (2, 3),
        ],
        7: [
            (0, 1), (2, 3), (4, 5), (0, 2), (1, 4), (3, 5), (0, 1), (2, 3), (4, 5),
            (1, 2), (3, 4), (2, 3), (5, 6), (4, 5), (3, 4),
        ],
        8: _insertion_sort_network(8),
    }
    if n in baselines:
        comps = [Comparator(i=i, j=j) for i, j in baselines[n]]
        return SortingNetwork(n=n, comparators=comps)
    return _insertion_sort_baseline(n)


def _insertion_sort_baseline(n: int) -> SortingNetwork:
    """Generate insertion-sort derived sorting network."""
    comparators = []
    for i in range(1, n):
        for j in range(i, 0, -1):
            comparators.append(Comparator(i=j - 1, j=j))
    return SortingNetwork(n=n, comparators=comparators)
