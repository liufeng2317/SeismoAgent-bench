from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.execution import ExperimentSpecError, expand_experiment, load_experiment_spec


class ExperimentSpecTests(unittest.TestCase):
    def test_expands_agent_task_variant_product_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "experiment.yaml"
            path.write_text(
                "experiment_id: smoke\noutput_root: /tmp/runs\nconcurrency: 2\n"
                "agents:\n  - id: a\n    name: agent-a\n    version: '1'\n    config: host.yaml\n    command: [python, agent.py]\n"
                "  - id: b\n    name: agent-b\n    version: '1'\n    config: bubble.yaml\n    command: [python, agent.py]\n"
                "tasks:\n  - id: task-one\n    task_spec: task.json\n    input_manifest: manifest.json\n    variants: [base, strict]\n",
                encoding="utf-8",
            )
            spec = load_experiment_spec(path)
            units = expand_experiment(spec)
            self.assertEqual([(u["agent_id"], u["variant"]) for u in units],
                             [("a", "base"), ("a", "strict"), ("b", "base"), ("b", "strict")])

    def test_rejects_duplicate_agent_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "experiment.yaml"
            path.write_text(
                "experiment_id: smoke\noutput_root: /tmp/runs\nconcurrency: 1\n"
                "agents:\n  - id: a\n    name: agent-a\n    version: '1'\n    config: host.yaml\n    command: [python, agent.py]\n  - id: a\n    name: agent-b\n    version: '1'\n    config: other.yaml\n    command: [python, agent.py]\n"
                "tasks:\n  - id: task-one\n    task_spec: task.json\n    input_manifest: manifest.json\n",
                encoding="utf-8",
            )
            with self.assertRaises(ExperimentSpecError):
                load_experiment_spec(path)


if __name__ == "__main__":
    unittest.main()
