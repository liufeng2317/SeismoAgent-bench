import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.task import render_agent_prompt
from tests.task_helpers import write_task_package


class PromptRenderingTests(unittest.TestCase):
    def test_renderer_combines_task_inputs_outputs_and_extra_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_task_package(root / "task.json", {
                "task_id": "prompt-task", "version": "1",
                "input_requirements": [{"id": "metadata", "data_type": "metadata", "required": True}],
                "evaluation": {"scorers": [{"name": "artifact-contract", "version": "1"}]},
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
            }, "Inspect the data.")
            (root / "manifest.json").write_text(json.dumps({
                "schema_version": 1, "case_id": "prompt_case", "entries": [{
                    "id": "metadata", "path": "/tmp/metadata.json", "type": "file", "notes": "metadata",
                }],
            }), encoding="utf-8")
            rendered = render_agent_prompt(root / "task.json", root / "manifest.json",
                                           extra_instructions="Use a concise report.")
            self.assertTrue(rendered.startswith("# Task: prompt-task\n"))
            self.assertNotIn("# SeismoAgentBench Task", rendered)
            self.assertIn("Inspect the data.", rendered)
            self.assertIn("available under `$BENCH_OUTPUT/input/`", rendered)
            self.assertIn("`input/` directory and everything below it are read-only", rendered)
            self.assertNotIn("/tmp/metadata.json", rendered)
            self.assertIn("result.json", rendered)
            self.assertIn("Use a concise report.", rendered)
            self.assertNotIn("### Task instructions", rendered)
            self.assertEqual(rendered.count("## Input data"), 1)
            self.assertEqual(rendered.count("## Structured output hints"), 1)

    def test_renderer_accepts_task_prompt_without_manifest_or_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / "task.json"
            task.write_text(json.dumps({
                "task_id": "prompt-only", "version": "1",
                "task_prompt_file": "task_prompt.md",
            }), encoding="utf-8")
            (root / "task_prompt.md").write_text(
                "Describe the required result in this prompt.\n", encoding="utf-8")
            rendered = render_agent_prompt(task)
            self.assertIn("Describe the required result", rendered)
            self.assertNotIn("## Input data", rendered)
            self.assertNotIn("## Structured output hints", rendered)


if __name__ == "__main__":
    unittest.main()
