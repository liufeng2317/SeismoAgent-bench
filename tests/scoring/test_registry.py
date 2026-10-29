import tempfile
import unittest
from pathlib import Path

from SeismoAgentBench.scoring import ScorerRegistryError, default_scorer_registry
from SeismoAgentBench.scoring.registry import ScorerContext, ScorerUnavailable


class ScorerRegistryTests(unittest.TestCase):
    def test_plans_declared_local_and_reference_scorers(self):
        registry = default_scorer_registry()
        plan = registry.plan({"evaluation": {"scorers": [
            {"name": "artifact-contract", "version": "1"},
            {"name": "catalog-basic", "version": "1"},
        ]}})
        self.assertEqual([item["mode"] for item in plan], ["local", "reference"])

    def test_catalog_metrics_finds_the_task_package_of_a_run(self):
        # <task>/runs/<variant>/<harness>/<model>/<run_id>/work: the handler must look for
        # <task>/evaluation/metrics.yaml, not one level too high or too low.
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp, "case", "runs", "min", "claude", "model", "run1", "work")
            work.mkdir(parents=True)
            handler = default_scorer_registry().resolve("catalog-metrics", "1").handler
            context = ScorerContext(task={}, output_dir=work, validation={})
            with self.assertRaises(ScorerUnavailable) as caught:
                handler(context)
            self.assertIn("metrics.yaml", str(caught.exception))
            self.assertIn(str(work.parent), str(caught.exception))

    def test_catalog_metrics_skips_a_run_outside_a_task_package(self):
        # A campaign run (<run_root>/<task_id>/<run_id>) is too shallow: a clear skip, not an IndexError.
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp, "task", "run1", "work")
            work.mkdir(parents=True)
            handler = default_scorer_registry().resolve("catalog-metrics", "1").handler
            with self.assertRaises(ScorerUnavailable) as caught:
                handler(ScorerContext(task={}, output_dir=work, validation={}))
            self.assertIn("<task>/runs/<variant>/<harness>/<model>/<run_id>", str(caught.exception))

    def test_unknown_scorer_is_rejected(self):
        with self.assertRaisesRegex(ScorerRegistryError, "not registered"):
            default_scorer_registry().plan({"evaluation": {"scorers": [
                {"name": "unknown", "version": "1"},
            ]}})


if __name__ == "__main__":
    unittest.main()
