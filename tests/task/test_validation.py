import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.task import ValidationError, load_json, validate_manifest, validate_task


TASK = {
    "task_id": "waveform-inspection",
    "version": "1",
    "task_prompt_file": "task_prompt.md",
    "output_contract": "output_contract.json",
    "input_requirements": [
        {"id": "waveforms", "data_type": "waveform", "required": True},
        {"id": "stations", "data_type": "station_metadata", "required": True},
    ],
    "evaluation": {"scorers": [{"name": "metadata-score", "version": "1"}]},
    "output_artifacts": [{"id": "summary", "path": "summary.json", "kind": "json", "required": True}],
}


def manifest():
    return {"schema_version": 1, "case_id": "synthetic_case", "entries": [
        {"id": "XX.TEST.HHZ", "path": "/tmp/waveform.mseed", "data_type": "waveform", "format": "miniSEED", "read_only": True,
         "channel": "HHZ", "start_time": "2020-01-01T00:00:00Z"},
        {"id": "station_metadata", "path": "/tmp/stations.xml", "data_type": "station_metadata", "format": "StationXML", "read_only": True},
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

    def test_manifest_rejects_missing_required_type(self):
        value = manifest(); value["entries"] = value["entries"][:1]
        with self.assertRaisesRegex(ValidationError, "missing required input types"):
            validate_manifest(value, task=TASK)

    def test_manifest_separates_semantic_type_from_file_format(self):
        value = manifest()
        value["entries"][0]["format"] = "miniSEED"
        value["entries"][1]["format"] = "StationXML"
        self.assertEqual(validate_manifest(value)["entries"][1]["data_type"], "station_metadata")
        value["entries"][1].pop("format")
        with self.assertRaisesRegex(ValidationError, "missing required field 'format'"):
            validate_manifest(value)

    def test_manifest_supports_directory_inputs(self):
        value = manifest()
        value["entries"][0]["path"] = "/tmp"
        value["entries"][0]["path_type"] = "directory"
        value["entries"][1]["path"] = "/etc/hosts"
        validate_manifest(value, check_paths=True)

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

    def test_task_accepts_framework_metadata(self):
        value = dict(
            TASK,
            category="seismology",
            software=["Python", "ObsPy"],
            required_system_packages=["libgomp"],
            taxonomy={"domain": "seismology", "methods": ["phase_picking"]},
            input_requirements=[
                {"id": "waveforms", "data_type": "waveform", "required": True},
            ],
            reference_requirements=[
                {"id": "reference_picks", "format": "CSV", "role": "scoring_only", "required": False},
            ],
            evaluation={"scorers": [{"name": "metadata-score", "version": "1"}]},
        )
        self.assertEqual(validate_task(value)["category"], "seismology")

    def test_task_metadata_rejects_malformed_requirements(self):
        value = dict(TASK, input_requirements=[{"id": "bad/id", "required": "yes"}])
        with self.assertRaisesRegex(ValidationError, r"input_requirements\[0\].id"):
            validate_task(value)

    def test_task_metadata_rejects_unknown_evaluation_fields(self):
        value = dict(TASK, evaluation={"scorers": [], "weights": {"x": 1}})
        with self.assertRaisesRegex(ValidationError, "task.evaluation has unknown field"):
            validate_task(value)

    def test_task_prompt_file_is_required(self):
        legacy = dict(TASK)
        legacy.pop("task_prompt_file")
        legacy["objective"] = "legacy wording"
        with self.assertRaisesRegex(ValidationError, "unknown field.*objective"):
            validate_task(legacy)

    def test_removed_task_fields_are_rejected(self):
        value = dict(TASK, input_types=["metadata"], scorer={"name": "old", "version": "1"})
        with self.assertRaisesRegex(ValidationError, "unknown field 'input_types'"):
            validate_task(value)

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
