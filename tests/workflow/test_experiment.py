import json
from pathlib import Path
import sys
import tempfile
import unittest

from SeismoAgentBench.workflow import execute_experiment


class ExperimentExecutionTests(unittest.TestCase):
    def test_executes_one_planned_unit_without_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "agent.py").write_text(
                "import json, os\n"
                "open(os.path.join(os.environ['BENCH_OUTPUT'], 'result.json'), 'w').write(json.dumps({'ok': True}))\n",
                encoding="utf-8",
            )
            (base / "task.json").write_text(json.dumps({
                "task_id": "experiment-task", "version": "1", "task_prompt": "test",
                "input_kinds": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
            (base / "manifest.json").write_text(json.dumps({
                "schema_version": 1, "case_id": "synthetic", "entries": [
                    {"id": "metadata", "path": "/tmp/metadata", "kind": "metadata", "read_only": True}
                ],
            }), encoding="utf-8")
            (base / "agent.yaml").write_text("harness: python\nmodel: null\nconfig: {}\n", encoding="utf-8")
            spec = base / "experiment.yaml"
            spec.write_text(
                "experiment_id: smoke\noutput_root: runs\nconcurrency: 1\n"
                "agents:\n  - id: demo\n    name: demo-agent\n    version: '1'\n    config: agent.yaml\n"
                f"    command: [{sys.executable}, {base / 'agent.py'}]\n"
                "tasks:\n  - id: task\n    task_spec: task.json\n    input_manifest: manifest.json\n    variants: [base]\n",
                encoding="utf-8",
            )
            results = execute_experiment(spec)
            self.assertEqual(len(results), 1)
            run = base / "runs" / "run_001_demo_base"
            self.assertEqual(results[0]["run"]["state"], "completed")
            self.assertTrue((run / "control/agent_config.yaml").is_file())
            self.assertTrue((run / "agent/output/result.json").is_file())
            self.assertFalse((run / "evaluation/score.json").exists())


if __name__ == "__main__":
    unittest.main()
