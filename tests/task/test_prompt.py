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
            self.assertTrue(rendered.startswith("<task_prompt>\n"))
            self.assertLess(rendered.index("<task_prompt>"), rendered.index("<framework_instructions>"))
            self.assertLess(rendered.index("<framework_instructions>"), rendered.index("<runtime_context>"))
            self.assertLess(rendered.index("<runtime_context>"), rendered.index("<additional_instructions>"))
            self.assertIn("</framework_instructions>", rendered)
            self.assertIn("</task_prompt>", rendered)
            self.assertIn("</runtime_context>", rendered)
            self.assertNotIn("# SeismoAgentBench Task", rendered)
            self.assertIn("Inspect the data.", rendered)
            self.assertIn("Input directory: `$BENCH_INPUT`", rendered)
            self.assertIn("Working directory: `$BENCH_WORK`", rendered)
            self.assertIn("Output directory: `$BENCH_OUTPUT`", rendered)
            self.assertIn("read-only", rendered)
            self.assertNotIn("/tmp/metadata.json", rendered)
            self.assertIn("result.json", rendered)
            self.assertIn("Use a concise report.", rendered)
            self.assertNotIn("### Task instructions", rendered)
            self.assertLess(rendered.index("## Working directory"), rendered.index("## Input data"))
            self.assertEqual(rendered.count("<runtime_context>"), 1)
            self.assertIn("<output_hints>", rendered)
            self.assertIn("## Declared output artifacts", rendered)
            self.assertIn("</output_hints>", rendered)
            self.assertLess(rendered.index("<output_hints>"), rendered.index("</output_hints>"))
            self.assertLess(rendered.index("</output_hints>"), rendered.index("</runtime_context>"))

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
            self.assertIn("## Input data", rendered)
            self.assertIn("Input directory: not configured for this run.", rendered)
            self.assertNotIn("<output_hints>", rendered)

    def test_time_budget_is_rendered_only_when_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = root / "task.json"
            task.write_text(json.dumps({
                "task_id": "budget-task", "version": "1",
                "task_prompt_file": "task_prompt.md",
            }), encoding="utf-8")
            (root / "task_prompt.md").write_text("Do the work.\n", encoding="utf-8")
            for budget, expected in ((172800, "Time budget: 172800 s (~48.0 h)"), (None, None)):
                with self.subTest(time_budget_s=budget):
                    runtime = {} if budget is None else {"time_budget_s": budget}
                    rendered = render_agent_prompt(task, runtime_context=runtime)
                    if expected is None:
                        self.assertNotIn("Time budget:", rendered)
                    else:
                        self.assertIn(expected, rendered)
                        self.assertIn("terminated at the deadline", rendered)


if __name__ == "__main__":
    unittest.main()
