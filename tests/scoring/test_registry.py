import unittest

from SeismoAgentBench.scoring import ScorerRegistryError, default_scorer_registry


class ScorerRegistryTests(unittest.TestCase):
    def test_plans_declared_local_and_reference_scorers(self):
        registry = default_scorer_registry()
        plan = registry.plan({"evaluation": {"scorers": [
            {"name": "artifact-contract", "version": "1"},
            {"name": "catalog-basic", "version": "1"},
        ]}})
        self.assertEqual([item["mode"] for item in plan], ["local", "reference"])

    def test_unknown_scorer_is_rejected(self):
        with self.assertRaisesRegex(ScorerRegistryError, "not registered"):
            default_scorer_registry().plan({"evaluation": {"scorers": [
                {"name": "unknown", "version": "1"},
            ]}})


if __name__ == "__main__":
    unittest.main()
