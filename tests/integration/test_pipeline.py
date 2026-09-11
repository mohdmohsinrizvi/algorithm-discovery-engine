"""Integration test: search -> verify -> benchmark -> storage."""

import os
import tempfile

from algorithm_discovery_lab.config.experiment import ExperimentConfig, SearchConfig
from algorithm_discovery_lab.experiments.runner import ExperimentRunner
from algorithm_discovery_lab.storage.db import Storage


class TestFullPipeline:
    def test_evolutionary_pipeline(self):
        config = ExperimentConfig(
            n=5,
            search=SearchConfig(
                algorithm="evolutionary",
                population_size=50,
                generations=50,
            ),
            seed=42,
            benchmark_repetitions=10,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            storage = Storage(db_path)
            runner = ExperimentRunner(config, storage)
            result = runner.run()

            assert result["experiment_id"].startswith("EXP-")
            assert result["elapsed_seconds"] > 0
            assert result["result"]["total_evaluated"] > 0

            # Check database
            experiments = storage.list_experiments()
            assert len(experiments) >= 1

            if result["discovery"]:
                discoveries = storage.list_discoveries()
                assert len(discoveries) >= 1

            storage.close()

    def test_random_search_pipeline(self):
        config = ExperimentConfig(
            n=4,
            search=SearchConfig(algorithm="random"),
            seed=42,
            benchmark_repetitions=10,
        )
        runner = ExperimentRunner(config)
        result = runner.run()

        assert result["result"]["total_evaluated"] > 0

    def test_search_produces_verified(self):
        config = ExperimentConfig(
            n=5,
            search=SearchConfig(
                algorithm="evolutionary",
                population_size=100,
                generations=100,
            ),
            seed=42,
            benchmark_repetitions=10,
        )
        runner = ExperimentRunner(config)
        result = runner.run()

        assert result["result"]["total_verified"] > 0
