import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.scoring import ScoreError, score_artifacts, validate_artifacts


TASK = {
    "task_id": "synthetic_catalog",
    "version": "1",
    "task_prompt_file": "task_prompt.md",
    "output_contract": "output_contract.json",
    "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
    "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
    "output_artifacts": [
        {"id": "summary", "path": "summary.json", "kind": "json", "required": True},
        {"id": "log", "path": "details.txt", "kind": "text", "required": False},
    ],
}


class ContractScoreTests(unittest.TestCase):
    def test_complete_inventory_gets_deterministic_contract_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "summary.json").write_text(json.dumps({"ok": True}))
            Path(tmp, "details.txt").write_text("done")
            validation = validate_artifacts(TASK, tmp)
            result = score_artifacts(TASK, validation)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["scorer"], {"name": "artifact-contract", "version": "1"})
            self.assertEqual(result["metrics"]["required_artifacts_present"], 1)
            self.assertEqual(result["metrics"]["optional_artifacts_present"], 1)
            self.assertEqual(result["metrics"]["total_bytes"], 16)
            self.assertEqual(result["metrics"]["contract_compliance"], 1.0)

    def test_missing_optional_artifact_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "summary.json").write_text("{}")
            result = score_artifacts(TASK, validate_artifacts(TASK, tmp))
            self.assertEqual(result["metrics"]["present_artifacts"], 1)
            self.assertEqual(result["metrics"]["optional_artifacts_present"], 0)

    def test_unvalidated_result_is_rejected(self):
        with self.assertRaisesRegex(ScoreError, "must pass"):
            score_artifacts(TASK, {"validated": False, "artifacts": []})

    def test_undeclared_inventory_artifact_is_rejected(self):
        validation = {"validated": True, "artifacts": [{"id": "other", "bytes": 1}]}
        with self.assertRaisesRegex(ScoreError, "undeclared"):
            score_artifacts(TASK, validation)

    def test_required_inventory_artifact_cannot_be_omitted(self):
        validation = {"validated": True, "artifacts": []}
        with self.assertRaisesRegex(ScoreError, "required artifacts"):
            score_artifacts(TASK, validation)


if __name__ == "__main__":
    unittest.main()
