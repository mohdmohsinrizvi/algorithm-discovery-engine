"""Tests for sorting network representation."""

import random

from algorithm_discovery_lab.problems.sorting_network import (
    Comparator,
    SortingNetwork,
    SortingNetworkProblem,
)


class TestComparator:
    def test_valid_comparator(self):
        c = Comparator(i=0, j=3)
        assert c.i == 0
        assert c.j == 3

    def test_invalid_comparator_rejects(self):
        try:
            Comparator(i=3, j=0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_equal_indices_rejects(self):
        try:
            Comparator(i=2, j=2)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_apply_swaps_when_needed(self):
        c = Comparator(i=0, j=1)
        assert c.apply([5, 3]) == [3, 5]

    def test_apply_no_swap_when_sorted(self):
        c = Comparator(i=0, j=1)
        assert c.apply([3, 5]) == [3, 5]

    def test_to_dict_roundtrip(self):
        c = Comparator(i=1, j=4)
        d = c.to_dict()
        c2 = Comparator.from_dict(d)
        assert c2.i == 1 and c2.j == 4


class TestSortingNetwork:
    def test_empty_network(self):
        net = SortingNetwork(n=4, comparators=[])
        assert net.comparator_count == 0
        assert net.depth == 0
        assert net.apply([4, 3, 2, 1]) == [4, 3, 2, 1]

    def test_single_comparator(self):
        net = SortingNetwork(n=2, comparators=[Comparator(0, 1)])
        assert net.comparator_count == 1
        assert net.depth == 1
        assert net.apply([2, 1]) == [1, 2]
        assert net.apply([1, 2]) == [1, 2]

    def test_baseline_n3_sorts(self):
        problem = SortingNetworkProblem(3)
        net = problem.get_baseline()
        assert net.apply([3, 2, 1]) == [1, 2, 3]
        assert net.apply([1, 2, 3]) == [1, 2, 3]
        assert net.apply([2, 1, 3]) == [1, 2, 3]

    def test_baseline_n5_sorts(self):
        problem = SortingNetworkProblem(5)
        net = problem.get_baseline()
        for _ in range(100):
            rng = random.Random(42)
            arr = rng.sample(range(100), 5)
            assert net.apply(arr) == sorted(arr)

    def test_baseline_n8_sorts(self):
        problem = SortingNetworkProblem(8)
        net = problem.get_baseline()
        for _ in range(50):
            rng = random.Random(42)
            arr = rng.sample(range(100), 8)
            assert net.apply(arr) == sorted(arr)

    def test_to_list_roundtrip(self):
        net = SortingNetwork(n=4, comparators=[Comparator(0, 1), Comparator(2, 3)])
        data = net.to_list()
        net2 = SortingNetwork.from_list(4, data)
        assert net2.n == 4
        assert len(net2.comparators) == 2
        assert net2.comparators[0].i == 0
        assert net2.comparators[1].j == 3

    def test_depth_calculation(self):
        # Two independent comparators in parallel: depth 1
        net = SortingNetwork(n=4, comparators=[Comparator(0, 1), Comparator(2, 3)])
        assert net.depth == 1

        # Two sequential comparators sharing a wire: depth 2
        net2 = SortingNetwork(n=3, comparators=[Comparator(0, 1), Comparator(1, 2)])
        assert net2.depth == 2


class TestSortingNetworkProblem:
    def test_init(self):
        problem = SortingNetworkProblem(5)
        assert problem.n == 5

    def test_generate_random(self):
        problem = SortingNetworkProblem(5)
        rng = random.Random(42)
        net = problem.generate_random_candidate(rng)
        assert net.n == 5
        assert len(net.comparators) > 0

    def test_is_valid(self):
        problem = SortingNetworkProblem(4)
        net = SortingNetwork(n=4, comparators=[Comparator(0, 1)])
        assert problem.is_valid(net)

    def test_is_valid_rejects_bad(self):
        problem = SortingNetworkProblem(4)
        net = SortingNetwork(n=4, comparators=[])
        assert not problem.is_valid(net)

    def test_fitness(self):
        problem = SortingNetworkProblem(4)
        net = problem.get_baseline()
        metrics = problem.fitness(net)
        assert "comparator_count" in metrics
        assert "depth" in metrics
        assert metrics["comparator_count"] > 0
        assert metrics["depth"] > 0

    def test_mutation_produces_valid(self):
        problem = SortingNetworkProblem(5)
        rng = random.Random(42)
        net = problem.get_baseline()
        for _ in range(50):
            mutated = problem.mutate(net, rng)
            assert problem.is_valid(mutated)

    def test_crossover_produces_valid(self):
        problem = SortingNetworkProblem(5)
        rng = random.Random(42)
        p1 = problem.generate_random_candidate(rng)
        p2 = problem.generate_random_candidate(rng)
        child = problem.crossover(p1, p2, rng)
        assert child.n == 5

    def test_serialize_roundtrip(self):
        problem = SortingNetworkProblem(5)
        net = problem.get_baseline()
        data = problem.serialize(net)
        net2 = problem.deserialize(data)
        assert net2.n == net.n
        assert len(net2.comparators) == len(net.comparators)
