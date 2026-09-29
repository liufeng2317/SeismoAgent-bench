import csv
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.scoring import PickScoreError, score_picks


def row(station, phase, time, status="picked"):
    return {"station": station, "phase": phase, "arrival_time_utc": time, "status": status}


class PickScoreTests(unittest.TestCase):
    def test_one_to_one_phase_matching_and_errors(self):
        result = score_picks(
            [row("CI.A", "P", "2019-07-05T00:00:00.20Z"),
             row("CI.A", "S", "2019-07-05T00:00:02Z"),
             row("CI.B", "P", "2019-07-05T00:01:00Z")],
            [row("CI.A", "P", "2019-07-05T00:00:00Z"),
             row("CI.A", "S", "2019-07-05T00:00:02.30Z"),
             row("CI.C", "P", "2019-07-05T00:01:00Z")],
            time_tolerance_s=0.5, reference_id="synthetic")
        self.assertEqual(result["status"], "scored")
        self.assertEqual(result["metrics"]["matched_picks"], 2)
        self.assertEqual(result["metrics"]["missing_reference_picks"], 1)
        self.assertEqual(result["metrics"]["per_phase"]["P"]["recall"], 0.5)
        self.assertAlmostEqual(result["metrics"]["per_phase"]["S"]["absolute_error_s"]["mean_s"], 0.3)

    def test_csv_schema_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                csv.writer(handle).writerow(["station", "phase"])
            with self.assertRaises(PickScoreError):
                score_picks(path, [row("CI.A", "P", "2019-07-05T00:00:00Z")])


if __name__ == "__main__":
    unittest.main()
