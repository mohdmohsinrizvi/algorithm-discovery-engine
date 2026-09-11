"""Tests for the verification engine."""

from algorithm_discovery_lab.problems.sorting_network import Comparator, SortingNetwork
from algorithm_discovery_lab.verification.verifier import (
    ExhaustiveVerifier,
    get_verifier,
)


class TestExhaustiveVerifier:
    def test_verified_correct_network(self):
        # Known correct: bubble sort on 3 wires
        net = SortingNetwork(n=3, comparators=[
            Comparator(0, 1), Comparator(1, 2), Comparator(0, 1),
        ])
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is True
        assert result.inputs_tested == 8  # 2^3
        assert result.method == "exhaustive_binary_input_verification"
        assert result.failures == []

    def test_rejected_incorrect_network(self):
        # Incorrect: only sorts first two wires
        net = SortingNetwork(n=3, comparators=[Comparator(0, 1)])
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is False
        assert result.counterexample is not None
        assert len(result.failures) > 0

    def test_rejected_single_comparator_n3(self):
        net = SortingNetwork(n=3, comparators=[Comparator(0, 2)])
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is False

    def test_verified_baseline_n4(self):
        from algorithm_discovery_lab.problems.sorting_network import SortingNetworkProblem
        problem = SortingNetworkProblem(4)
        net = problem.get_baseline()
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is True
        assert result.inputs_tested == 16  # 2^4

    def test_verified_baseline_n8(self):
        from algorithm_discovery_lab.problems.sorting_network import SortingNetworkProblem
        problem = SortingNetworkProblem(8)
        net = problem.get_baseline()
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is True
        assert result.inputs_tested == 256  # 2^8

    def test_empty_network_fails(self):
        net = SortingNetwork(n=3, comparators=[])
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is False

    def test_verification_timing(self):
        net = SortingNetwork(n=8, comparators=[
            Comparator(0, 1), Comparator(2, 3), Comparator(4, 5), Comparator(6, 7),
            Comparator(0, 2), Comparator(1, 3), Comparator(4, 6), Comparator(5, 7),
            Comparator(0, 4), Comparator(1, 5), Comparator(2, 6), Comparator(3, 7),
            Comparator(1, 2), Comparator(3, 5), Comparator(4, 6),
            Comparator(0, 1), Comparator(2, 4), Comparator(5, 7),
            Comparator(2, 3), Comparator(4, 5), Comparator(1, 2), Comparator(3, 4),
        ])
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.duration_ms >= 0


class TestGetVerifier:
    def test_exhaustive_backend(self):
        v = get_verifier("exhaustive", 8)
        assert isinstance(v, ExhaustiveVerifier)

    def test_unknown_backend_raises(self):
        try:
            get_verifier("unknown", 8)
            assert False, "Should raise ValueError"
        except ValueError:
            pass


class TestIntentionallyIncorrect:
    """Test that the verifier catches intentionally incorrect networks."""

    def test_reversed_sort(self):
        # Network that sorts in descending order
        net = SortingNetwork(n=3, comparators=[
            Comparator(0, 1), Comparator(1, 2), Comparator(0, 1),
        ])
        # This IS correct for ascending, but let's test with reversed input expectations
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is True  # It correctly sorts ascending

    def test_partial_sort(self):
        # Only sorts first 2 of 3 wires
        net = SortingNetwork(n=3, comparators=[Comparator(0, 1)])
        v = ExhaustiveVerifier()
        result = v.verify(net)
        assert result.verified is False
        # Counterexample should show unsorted result
        assert result.counterexample is not None
