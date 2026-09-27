import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.scoring import ArtifactValidationError, validate_artifacts


def task(required=True):
    return {"output_artifacts": [
        {"id": "summary", "path": "summary.json", "kind": "json", "required": required},
        {"id": "log", "path": "details.txt", "kind": "text", "required": False},
    ]}


class ArtifactTests(unittest.TestCase):
    def test_valid_required_json_and_missing_optional(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "summary.json").write_text(json.dumps({"ok": True}))
            result = validate_artifacts(task(), tmp)
            self.assertTrue(result["validated"])
            self.assertEqual([x["id"] for x in result["artifacts"]], ["summary"])

    def test_missing_required_artifact_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ArtifactValidationError, "required artifact is missing"):
                validate_artifacts(task(), tmp)

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "summary.json").write_text("not json")
            with self.assertRaisesRegex(ArtifactValidationError, "not valid JSON"):
                validate_artifacts(task(), tmp)

    def test_symlink_artifact_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp, "outside.json"); source.write_text("{}")
            Path(tmp, "summary.json").symlink_to(source)
            with self.assertRaisesRegex(ArtifactValidationError, "regular file"):
                validate_artifacts(task(), tmp)

    def test_nested_artifact_is_allowed_but_parent_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "nested").mkdir(); Path(tmp, "nested/summary.json").write_text("{}")
            nested = {"output_artifacts": [{"id": "summary", "path": "nested/summary.json", "kind": "json", "required": True}]}
            self.assertTrue(validate_artifacts(nested, tmp)["validated"])
            unsafe = {"output_artifacts": [{"id": "summary", "path": "../summary.json", "kind": "json", "required": True}]}
            with self.assertRaises(ArtifactValidationError):
                validate_artifacts(unsafe, tmp)


if __name__ == "__main__":
    unittest.main()
