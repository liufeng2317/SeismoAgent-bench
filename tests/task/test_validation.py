import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.task import ValidationError, load_json, validate_manifest, validate_task


TASK = {
    "task_id": "waveform-inspection",
    "version": "1",
    "objective": "Inspect declared waveform metadata.",
    "input_kinds": ["waveform", "stationxml"],
    "output_artifacts": [{"id": "summary", "kind": "json", "required": True}],
    "scorer": {"name": "metadata-score", "version": "1"},
}


def manifest():
    return {"schema_version": 1, "case_id": "synthetic_case", "entries": [
        {"id": "XX.TEST.HHZ", "path": "/tmp/waveform.mseed", "kind": "waveform", "read_only": True,
         "channel": "HHZ", "start_time": "2020-01-01T00:00:00Z"},
        {"id": "stationxml", "path": "/tmp/stations.xml", "kind": "stationxml", "read_only": True},
    ]}


class ValidationTests(unittest.TestCase):
    def test_valid_task_and_manifest(self):
        self.assertEqual(validate_task(TASK)["task_id"], "waveform-inspection")
        self.assertEqual(len(validate_manifest(manifest(), task=TASK)["entries"]), 2)

    def test_manifest_rejects_duplicate_ids_and_writable_entry(self):
        value = manifest()
        value["entries"][1]["id"] = value["entries"][0]["id"]
        value["entries"][1]["read_only"] = False
        with self.assertRaises(ValidationError) as raised:
            validate_manifest(value)
        self.assertIn("duplicate manifest entry id", str(raised.exception))
        self.assertIn("read_only must be true", str(raised.exception))

    def test_manifest_rejects_missing_required_kind(self):
        value = manifest(); value["entries"] = value["entries"][:1]
        with self.assertRaisesRegex(ValidationError, "missing required input kinds"):
            validate_manifest(value, task=TASK)

    def test_manifest_path_check_is_optional_and_read_only(self):
        value = manifest()
        validate_manifest(value, check_paths=False)
        with self.assertRaisesRegex(ValidationError, "not an existing regular file"):
            validate_manifest(value, check_paths=True)

    def test_task_rejects_unknown_fields_and_duplicate_outputs(self):
        value = dict(TASK, extra="not allowed")
        value["output_artifacts"] = [TASK["output_artifacts"][0], TASK["output_artifacts"][0]]
        with self.assertRaises(ValidationError) as raised:
            validate_task(value)
        self.assertIn("unknown field", str(raised.exception))
        self.assertIn("duplicate task output artifact id", str(raised.exception))

    def test_load_json_requires_object_and_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "task.json"
            path.write_text(json.dumps(TASK), encoding="utf-8")
            before = path.read_bytes()
            self.assertEqual(load_json(path), TASK)
            self.assertEqual(path.read_bytes(), before)
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValidationError):
                load_json(path)


if __name__ == "__main__":
    unittest.main()
