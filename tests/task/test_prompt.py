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
                    "id": "metadata", "path": "/tmp/metadata.json", "data_type": "metadata",
                    "format": "JSON", "read_only": True,
                }],
            }), encoding="utf-8")
            rendered = render_agent_prompt(root / "task.json", root / "manifest.json",
                                           extra_instructions="Use a concise report.")
            self.assertIn("Inspect the data.", rendered)
            self.assertIn("/tmp/metadata.json", rendered)
            self.assertIn("result.json", rendered)
            self.assertIn("Use a concise report.", rendered)
            self.assertNotIn("### Task instructions", rendered)
            self.assertEqual(rendered.count("## Input data"), 1)
            self.assertEqual(rendered.count("## Required outputs"), 1)


if __name__ == "__main__":
    unittest.main()
