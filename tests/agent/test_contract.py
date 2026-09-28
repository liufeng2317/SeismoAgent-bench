import json
from pathlib import Path
import sys
import tempfile
import unittest

from SeismoAgentBench.agent import AgentError, AgentSpec, run_agent
from SeismoAgentBench.workflow import evaluate_run


TASK = {
    "task_id": "agent-smoke",
    "version": "1",
    "task_prompt": "Run a synthetic agent.",
    "input_types": ["metadata"],
    "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
    "scorer": {"name": "artifact-contract", "version": "1"},
}
MANIFEST = {"schema_version": 1, "case_id": "synthetic_case", "entries": [
    {"id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata", "format": "JSON", "read_only": True}
]}


class AgentContractTests(unittest.TestCase):
    def test_spec_rejects_invalid_identity_and_empty_command(self):
        with self.assertRaises(AgentError):
            AgentSpec.from_command("bad name", "1", ["echo"])
        with self.assertRaises(AgentError):
            AgentSpec.from_command("demo", "1", [])

    def test_agent_runs_through_standard_workflow_and_records_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "runs"
            root.mkdir()
            task = base / "task.json"
            manifest = base / "manifest.json"
            task.write_text(json.dumps(TASK), encoding="utf-8")
            manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")
            code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'result.json'),'w').write(json.dumps({'agent': True}))"
            spec = AgentSpec.from_command("synthetic-agent", "0.1", [sys.executable, "-c", code])
            result = run_agent(task, manifest, spec, root, "run-001", timeout=10)
            run = root / "run-001"
            self.assertEqual(result["run"]["state"], "completed")
            self.assertEqual(json.loads((run / "record/agent_command.json").read_text())["name"], "synthetic-agent")
            self.assertEqual(json.loads((run / "record/run_result.json").read_text())["agent"]["version"], "0.1")
            evaluated = evaluate_run(run)
            self.assertEqual(evaluated["run"]["state"], "scored")


if __name__ == "__main__":
    unittest.main()
