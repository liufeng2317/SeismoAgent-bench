import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from SeismoAgentBench.scoring import ReferenceSpec, validate_catalog
from SeismoAgentBench.task import TaskRegistry, load_json, validate_manifest, validate_task


PACKAGE = Path(__file__).resolve().parents[2] / "tasks" / "2019_ridgecrest_california"


class RidgecrestPackageTests(unittest.TestCase):
    def test_task_and_input_manifest_are_valid(self):
        task = validate_task(load_json(PACKAGE / "task.json"))
        manifest = validate_manifest(load_json(PACKAGE / "input_manifest.json"), task=task)
        self.assertEqual(manifest["case_id"], "2019_ridgecrest_california")
        self.assertEqual(len(manifest["entries"]), 4)

    def test_registry_discovers_case_task_without_expert_outputs(self):
        registry = TaskRegistry.from_directory(PACKAGE)
        self.assertEqual(registry.load("ridgecrest_2019_catalog_smoke", "1")["task_id"],
                         "ridgecrest_2019_catalog_smoke")

    def test_smoke_reference_manifest_and_catalog_are_valid(self):
        manifest = PACKAGE / "references/usgs_mainshocks/reference_manifest.json"
        reference = ReferenceSpec.from_manifest(manifest)
        catalog = reference.load_catalog()
        self.assertEqual(len(catalog["events"]), 2)
        self.assertEqual(catalog["events"][1]["magnitude"], 7.1)
        self.assertEqual(validate_catalog(json.loads(reference.path.read_text()))["catalog_id"],
                         "ridgecrest-usgs-mainshocks-smoke")

    def test_case_package_runs_through_cli_without_scientific_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            code = "import json,os; open(os.path.join(os.environ['BENCH_OUTPUT'],'catalog.json'),'w').write(json.dumps({'schema_version':1,'catalog_id':'dry-run','events':[]}))"
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent",
                       "--task", str(PACKAGE / "task.json"),
                       "--manifest", str(PACKAGE / "input_manifest.json"),
                       "--agent-name", "ridgecrest-infrastructure-dry-run",
                       "--agent-version", "1",
                       "--run-root", str(run_root),
                       "--run-id", "smoke-001",
                       "--reference-manifest", str(PACKAGE / "references/usgs_mainshocks/reference_manifest.json"),
                       "--", sys.executable, "-c", code]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "scored")
            self.assertEqual(payload["scientific_score"]["metrics"]["candidate_events"], 0)
            self.assertEqual(payload["scientific_score"]["metrics"]["reference_events"], 2)
            self.assertTrue((run_root / "smoke-001/score/task_summary.json").is_file())

    def test_deterministic_baseline_generates_and_scores_candidate_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs"
            command = [sys.executable, "-m", "SeismoAgentBench", "run-agent",
                       "--task", str(PACKAGE / "task.json"),
                       "--manifest", str(PACKAGE / "input_manifest.json"),
                       "--agent-name", "ridgecrest-deterministic-baseline",
                       "--agent-version", "1",
                       "--run-root", str(run_root),
                       "--run-id", "baseline-001",
                       "--reference-manifest", str(PACKAGE / "references/usgs_mainshocks/reference_manifest.json"),
                       "--", sys.executable, str(PACKAGE / "baseline_agent.py")]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["run"]["state"], "scored")
            metrics = payload["scientific_score"]["metrics"]
            self.assertEqual(metrics["candidate_events"], 2)
            self.assertEqual(metrics["matched_events"], 2)
            self.assertEqual(metrics["precision"], 1.0)
            self.assertEqual(metrics["recall"], 1.0)
            self.assertTrue((run_root / "baseline-001/output/catalog.json").is_file())
            self.assertTrue((run_root / "baseline-001/evaluation_report.json").is_file())


if __name__ == "__main__":
    unittest.main()
