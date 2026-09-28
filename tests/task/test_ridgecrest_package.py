import json
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
