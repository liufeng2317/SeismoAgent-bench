import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from SeismoAgentBench.scoring import ScoreError
from SeismoAgentBench.workflow import run_task
from tests.task_helpers import write_task_package


TASK = {
    "task_id": "pipeline-smoke",
    "version": "1",
    "task_prompt_file": "task_prompt.md",
    "output_contract": "output_contract.json",
    "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
    "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
    "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
}
MANIFEST = {"schema_version": 1, "case_id": "synthetic_case", "entries": [
    {"id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata", "format": "JSON", "read_only": True}
]}


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "runs"
        self.root.mkdir()
        self.task = base / "task.json"
        self.manifest = base / "manifest.json"
        write_task_package(self.task, TASK, "Run a synthetic end-to-end task.")
        self.manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_success_runs_validation_and_score(self):
        code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'result.json'),'w').write(json.dumps({'ok': True}))"
        result = run_task(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-001", timeout=10)
        run = self.root / "run-001"
        self.assertEqual(result["run"]["state"], "scored")
        self.assertEqual(result["score"]["metrics"]["contract_compliance"], 1.0)
        self.assertTrue((run / "record/artifact_manifest.json").is_file())
        self.assertTrue((run / "evaluation/score.json").is_file())
        environment = json.loads((run / "record/environment.json").read_text())
        self.assertEqual(environment["execution_profile"], "trusted-development")
        report = json.loads((run / "evaluation/report.json").read_text())
        self.assertEqual(report["records"]["score"], "evaluation/score.json")
        self.assertIsNone(report["agent"])

    def test_missing_required_output_is_not_scored(self):
        result = run_task(self.task, self.manifest, [sys.executable, "-c", "pass"], self.root, "run-002", timeout=10)
        self.assertEqual(result["run"]["state"], "artifact_invalid")
        self.assertIsNone(result["score"])
        self.assertFalse((self.root / "run-002/evaluation/score.json").exists())
        self.assertEqual(json.loads((self.root / "run-002/evaluation/report.json").read_text())["state"], "artifact_invalid")

    def test_command_failure_is_not_scored(self):
        result = run_task(self.task, self.manifest, [sys.executable, "-c", "raise SystemExit(9)"], self.root, "run-003", timeout=10)
        self.assertEqual(result["run"]["state"], "execution_failed")
        self.assertIsNone(result["score"])

    def test_scoring_failure_is_recorded(self):
        code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'result.json'),'w').write(json.dumps({'ok': True}))"
        with patch("SeismoAgentBench.workflow.evaluate_run.score_artifacts", side_effect=ScoreError("synthetic scorer failure")):
            result = run_task(self.task, self.manifest, [sys.executable, "-c", code], self.root, "run-004", timeout=10)
        self.assertEqual(result["run"]["state"], "scoring_failed")
        self.assertEqual(result["score"]["status"], "scoring_failed")

    def test_reference_manifest_enables_optional_scientific_scoring(self):
        base = Path(self.tmp.name)
        task = base / "catalog-task.json"
        write_task_package(task, {
            **TASK,
            "task_id": "catalog-pipeline-smoke",
            "output_artifacts": [{"id": "catalog", "path": "catalog.json", "kind": "catalog", "required": True}],
        }, "Run a synthetic catalog task.")
        reference_catalog = base / "reference.json"
        reference_catalog.write_text(json.dumps({
            "schema_version": 1,
            "catalog_id": "reference",
            "events": [{"event_id": "ref-1", "origin_time": "2019-07-04T17:00:00Z",
                         "latitude": 35.7, "longitude": -117.5, "depth_km": 8.0}],
        }), encoding="utf-8")
        reference_manifest = base / "reference_manifest.json"
        reference_manifest.write_text(json.dumps({
            "schema_version": 1,
            "reference_id": "synthetic-reference",
            "version": "1",
            "role": "location",
            "path": str(reference_catalog),
        }), encoding="utf-8")
        code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'catalog.json'),'w').write(json.dumps({'schema_version':1,'catalog_id':'candidate','events':[{'event_id':'cand-1','origin_time':'2019-07-04T17:00:01Z','latitude':35.7,'longitude':-117.5,'depth_km':8.0}]}))"
        result = run_task(task, self.manifest, [sys.executable, "-c", code], self.root, "run-005",
                          timeout=10, reference_manifest=reference_manifest)
        run = self.root / "run-005"
        self.assertEqual(result["run"]["state"], "scored")
        self.assertEqual(result["scientific_score"]["metrics"]["matched_events"], 1)
        self.assertTrue((run / "evaluation/scientific_score.json").is_file())
        self.assertTrue((run / "evaluation/task_summary.json").is_file())
        self.assertEqual(json.loads((run / "evaluation/report.json").read_text())["reference"]["reference_id"], "synthetic-reference")


if __name__ == "__main__":
    unittest.main()
