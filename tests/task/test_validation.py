import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.task import ValidationError, validate_manifest, validate_task


TASK = {
    "task_id": "input-validation",
    "version": "1",
    "task_prompt_file": "task_prompt.md",
}


def manifest():
    return {"schema_version": 1, "case_id": "synthetic_case", "entries": [
        {"id": "waveforms", "path": "/tmp/waveforms", "type": "folder", "notes": "waveforms"},
        {"id": "stations", "path": "/tmp/stations.xml", "type": "file", "notes": "stations"},
    ]}


class ValidationTests(unittest.TestCase):
    def test_task_prompt_is_valid_without_manifest_or_output_contract(self):
        self.assertEqual(validate_task(TASK)["task_id"], "input-validation")

    def test_valid_task_and_manifest(self):
        self.assertEqual(len(validate_manifest(manifest(), task=TASK)["entries"]), 2)

    def test_manifest_rejects_duplicate_ids(self):
        value = manifest()
        value["entries"][1]["id"] = value["entries"][0]["id"]
        with self.assertRaisesRegex(ValidationError, "duplicate manifest entry id"):
            validate_manifest(value)

    def test_manifest_accepts_only_file_or_folder_types(self):
        value = manifest()
        value["entries"][0]["type"] = "waveform"
        with self.assertRaisesRegex(ValidationError, "type must be file or folder"):
            validate_manifest(value)

    def test_manifest_rejects_unknown_entry_fields(self):
        value = manifest()
        value["entries"][0]["data_type"] = "waveform"
        with self.assertRaisesRegex(ValidationError, "unknown field"):
            validate_manifest(value)

    def test_manifest_path_check_is_optional_and_read_only(self):
        value = manifest()
        validate_manifest(value, check_paths=False)
        with self.assertRaisesRegex(ValidationError, "not an existing"):
            validate_manifest(value, check_paths=True)

    def test_manifest_supports_existing_file_and_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "waveforms").mkdir()
            (root / "stations.xml").write_text("station", encoding="utf-8")
            value = manifest()
            value["entries"][0]["path"] = str(root / "waveforms")
            value["entries"][1]["path"] = str(root / "stations.xml")
            validate_manifest(value, check_paths=True)

    def test_task_rejects_unknown_fields(self):
        with self.assertRaises(ValidationError):
            validate_task(dict(TASK, extra="not allowed"))


if __name__ == "__main__":
    unittest.main()
