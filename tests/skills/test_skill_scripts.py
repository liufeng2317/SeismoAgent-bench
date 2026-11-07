"""Scripts bundled with the Agent skills (data/agent_resource/skills/*/scripts).

Each guards against an error seen in development runs: products written one level too deep and dispositions
without evidence (check_submission), a noisy pick group adopted (compare_pick_groups), unconstrained events
piled at a grid edge (expectation_hypocentres), events beyond the network kept (drop_beyond_network).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "data/agent_resource/skills"
CHECKER = ROOT / "seismo_checker"


def run(script: Path, *args, env=None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, env=env)


class SubmissionCheckTests(unittest.TestCase):
    def test_flags_products_in_work_subdirectory_and_dispositions_without_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "work").mkdir()
            (out / "work/catalog.csv").write_text("event_id\n")
            (out / "checker/final").mkdir(parents=True)
            (out / "checker/final/checker_report.json").write_text(json.dumps({"flags": [{"flag_id": "space.depth_layers"}]}))
            (out / "checker/dispositions.json").write_text(json.dumps({"space.depth_layers": "justified"}))
            r = run(SKILLS / "catalog-checker/scripts/check_submission.py", "--output-dir", out)
            self.assertEqual(r.returncode, 1)
            self.assertIn("catalog.csv: missing at the top", r.stdout)
            self.assertIn("work/catalog.csv exists", r.stdout)
            self.assertIn("justified without evidence", r.stdout)


class PickGroupTests(unittest.TestCase):
    def test_noisy_p_only_group_has_a_large_spread_ratio(self):
        rng = np.random.default_rng(0)
        rows = []
        for st, sd, phases in (("A.QUIET1", 0.08, "PS"), ("A.QUIET2", 0.08, "PS"), ("A.QUIET3", 0.08, "PS"), ("B.NOISY", 0.6, "P")):
            for ph in phases:
                for r in rng.normal(0, sd, 50):
                    rows.append({"station_id": st, "phase": ph, "residual_s": r})
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "picks.csv"
            pd.DataFrame(rows).to_csv(f, index=False)
            r = run(SKILLS / "catalog-knowledge/scripts/compare_pick_groups.py", "--picks", f, "--p-only")
            rep = json.loads(r.stdout)
            self.assertEqual(rep["group_stations"], ["B.NOISY"])
            self.assertGreater(rep["residuals"]["spread_ratio"], 4)


class ExpectationTests(unittest.TestCase):
    def test_events_at_the_grid_top_take_their_expectation_depth(self):
        ev = pd.DataFrame({"event_id": ["e1", "e2", "e3"], "status": "LOCATED", "latitude": 40.0, "longitude": -112.0,
                           "depth_km": [-1.0, 8.0, 12.0], "x_km": 0.0, "y_km": 0.0, "erz_km": [6.0, 1.0, 1.0],
                           "expect_x_km": [1.0, 0.0, 0.0], "expect_y_km": 0.0, "expect_depth_km": [5.0, 8.0, 12.0]})
        cat = pd.DataFrame({"event_id": ["e1", "e2", "e3"], "latitude": 40.0, "longitude": -112.0, "depth_km": [-1.0, 8.0, 12.0]})
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            ev.to_csv(d / "events.csv", index=False)
            cat.to_csv(d / "catalog.csv", index=False)
            run(SKILLS / "catalog-knowledge/scripts/expectation_hypocentres.py", "--events", d / "events.csv",
                "--catalog", d / "catalog.csv", "--output", d / "out.csv", "--changes", d / "changes.csv", "--grid-top", -1.0,
                "--grid-bottom", 30.0)
            out = pd.read_csv(d / "out.csv").set_index("event_id")
            self.assertAlmostEqual(out.loc["e1", "depth_km"], 5.0)
            self.assertGreater(out.loc["e1", "longitude"], -112.0)  # 1 km east
            self.assertAlmostEqual(out.loc["e2", "depth_km"], 8.0)


class BeyondNetworkTests(unittest.TestCase):
    def test_events_far_outside_the_station_hull_are_rejected(self):
        st = pd.DataFrame({"station_id": ["XX.S1", "XX.S2", "XX.S3", "XX.S4"], "latitude": [40.0, 40.0, 40.2, 40.2],
                           "longitude": [-112.0, -111.8, -112.0, -111.8], "elevation_m": 1500.0})
        cat = pd.DataFrame({"event_id": ["in", "out"], "origin_time_utc": "2020-01-01T00:00:00Z", "latitude": [40.1, 41.0],
                            "longitude": [-111.9, -111.9], "depth_km": 5.0, "magnitude": 1.0, "status": "accepted"})
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            st.to_csv(d / "stations.csv", index=False)
            cat.to_csv(d / "catalog.csv", index=False)
            r = run(SKILLS / "catalog-knowledge/scripts/drop_beyond_network.py", "--checker", CHECKER, "--catalog",
                    d / "catalog.csv", "--stations", d / "stations.csv", "--output", d / "out.csv")
            self.assertEqual(r.returncode, 0, r.stderr)
            out = pd.read_csv(d / "out.csv").set_index("event_id")
            self.assertEqual(out.loc["out", "status"], "rejected")
            self.assertEqual(out.loc["in", "status"], "accepted")


if __name__ == "__main__":
    unittest.main()
