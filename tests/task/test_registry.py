import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.task import TaskRegistry, TaskRegistryError


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic_task" / "task.json"


class TaskRegistryTests(unittest.TestCase):
    def test_register_and_load_fixture_by_identity(self):
        registry = TaskRegistry()
        record = registry.register(FIXTURE)
        self.assertEqual((record.task_id, record.version), ("synthetic_catalog_smoke", "1"))
        loaded = registry.load("synthetic_catalog_smoke", "1")
        self.assertEqual(loaded["task_id"], "synthetic_catalog_smoke")
        self.assertEqual([item.task_id for item in registry.records()], ["synthetic_catalog_smoke"])

    def test_directory_discovery_only_registers_task_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one").mkdir()
            (root / "one/task.json").write_text(FIXTURE.read_text(), encoding="utf-8")
            for name in ("task_prompt.md", "output_contract.json"):
                (root / "one" / name).write_bytes((FIXTURE.parent / name).read_bytes())
            (root / "one/manifest.json").write_text("{}", encoding="utf-8")
            registry = TaskRegistry.from_directory(root)
            self.assertEqual(len(registry.records()), 1)

    def test_duplicate_identity_and_ambiguous_version_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "one.json"
            second = root / "two.json"
            task = json.loads(FIXTURE.read_text())
            first.parent.joinpath("task_prompt.md").write_text("test\n", encoding="utf-8")
            first.parent.joinpath("output_contract.json").write_bytes((FIXTURE.parent / "output_contract.json").read_bytes())
            first.write_text(json.dumps(task), encoding="utf-8")
            task["version"] = "2"
            second.write_text(json.dumps(task), encoding="utf-8")
            registry = TaskRegistry()
            registry.register(first)
            with self.assertRaisesRegex(TaskRegistryError, "already registered"):
                registry.register(first)
            registry.register(second)
            with self.assertRaisesRegex(TaskRegistryError, "ambiguous"):
                registry.load("synthetic_catalog_smoke")


if __name__ == "__main__":
    unittest.main()
