from pathlib import Path
import unittest

from SeismoAgentBench.execution import RunLayout, RunLayoutError


class RunLayoutTests(unittest.TestCase):
    def test_builds_canonical_unit_path(self):
        layout = RunLayout(Path("/ai4earthafs/runs"), "campaign_20260928",
                           "ridgecrest_2019_phase_picking", "base",
                           "codex_gpt6_astra", "run_001")
        self.assertEqual(
            layout.unit_root,
            Path("/ai4earthafs/runs/campaign_20260928/ridgecrest_2019_phase_picking/base/codex_gpt6_astra/run_001"),
        )
        self.assertEqual(layout.run_root, layout.unit_root.parent)

    def test_rejects_relative_root_and_unsafe_component(self):
        with self.assertRaises(RunLayoutError):
            RunLayout(Path("relative"), "campaign", "task", "base", "agent", "run")
        with self.assertRaises(RunLayoutError):
            RunLayout(Path("/runs"), "campaign", "task/id", "base", "agent", "run")


if __name__ == "__main__":
    unittest.main()
