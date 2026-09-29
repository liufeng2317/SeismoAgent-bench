import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.task import render_agent_prompt


class PromptRenderingTests(unittest.TestCase):
    def test_renderer_combines_task_inputs_outputs_and_extra_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "task.json").write_text(json.dumps({
                "task_id": "prompt-task", "version": "1", "task_prompt": "Inspect the data.",
                "input_types": ["metadata"],
                "output_artifacts": [{"id": "result", "path": "result.json", "kind": "json", "required": True}],
                "scorer": {"name": "artifact-contract", "version": "1"},
            }), encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
