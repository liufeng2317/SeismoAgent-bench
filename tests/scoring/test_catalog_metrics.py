"""Pre-registered catalog metrics v1: matching and metric semantics on synthetic catalogs."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from SeismoAgentBench.scoring.catalog_metrics.audit import audited_false_rate
from SeismoAgentBench.scoring.catalog_metrics.dimensions import b_value, magnitude_classes
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond, match
from SeismoAgentBench.scoring.catalog_metrics.metrics import (
    ceilings, depth_profile, location, m90, off_structure_fraction, pair_distance_error, union_support)
from SeismoAgentBench.scoring.catalog_metrics.tables import Population, standardize

T0 = pd.Timestamp("2020-01-01T00:00:00Z")
CENTER = (-100.0, 40.0)


def population(key, seconds, lat=None, lon=None, depth=None, mag=None, roles="DLS", time_only=False):
    n = len(seconds)
    frame = pd.DataFrame({"time": [T0 + pd.Timedelta(seconds=s) for s in seconds],
                          "latitude": lat if lat is not None else [np.nan] * n,
                          "longitude": lon if lon is not None else [np.nan] * n,
                          "depth_km": depth if depth is not None else [np.nan] * n,
                          "magnitude": mag if mag is not None else [np.nan] * n})
    return Population(key=key, events=standardize(frame), roles=frozenset(roles), time_only=time_only)


class MatchingTest(unittest.TestCase):
    def test_greedy_one_to_one_prefers_the_nearer_event(self):
        # Two candidates compete for one reference event; the nearer one wins and the
        # other may not reuse it, even though both are inside the gates.
        ref = population("ref", [10.0], [40.0], [-100.0])
        cand = population("cand", [10.5, 10.1], [40.01, 40.05], [-100.0, -100.0])
        pairs = match(cand, ref, 4.0, 15.0)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(int(pairs.a[0]), int(np.argmin(np.abs(cand.events.latitude - 40.0))))

    def test_gates_bound_time_and_distance(self):
        ref = population("ref", [0.0, 100.0], [40.0, 40.0], [-100.0, -100.0])
        cand = population("cand", [4.5, 100.0], [40.0, 40.2], [-100.0, -100.0])  # 4.5 s late; 22 km off
        self.assertEqual(len(match(cand, ref, 4.0, 15.0)), 0)

    def test_time_only_recall_is_chance_corrected(self):
        # A dense time-only reference matches a random candidate by coincidence; the
        # 60-s shifted run must remove that share.
        rng = np.random.default_rng(1)
        ref = population("shelly", np.sort(rng.uniform(0, 3600, 600)), roles="D", time_only=True)
        cand = population("cand", np.sort(rng.uniform(0, 3600, 300)), [40.0] * 300, [-100.0] * 300)
        result = correspond(cand, ref)
        self.assertIsNone(result["gates"][1])
        self.assertGreater(len(result["pairs"]), 0)
        net = (len(result["pairs"]) - result["chance"]) / 600
        self.assertLess(abs(net), 0.05)


class MetricTest(unittest.TestCase):
    def test_ceiling_is_the_best_other_reference(self):
        times = np.arange(0, 1000, 10.0)
        lat, lon = [40.0] * 100, [-100.0] * 100
        r = population("r", times, lat, lon)
        half = population("half", times[:50], lat[:50], lon[:50])
        most = population("most", times[:80], lat[:80], lon[:80])
        value = ceilings({"r": r, "half": half, "most": most})["r"]
        self.assertEqual(value["by"], "most")
        self.assertAlmostEqual(value["value"], 0.8)

    def test_m90_is_the_lowest_magnitude_with_recall_090(self):
        mags = np.round(np.repeat(np.arange(0.0, 3.0, 0.5), 20), 1)
        hit = mags >= 1.0
        self.assertEqual(m90(mags, hit), 1.0)
        self.assertIsNone(m90(mags, np.zeros_like(hit)))

    def test_pair_distance_error_ignores_a_common_frame_shift(self):
        rng = np.random.default_rng(2)
        n = 200
        lat, lon = 40 + rng.normal(0, 0.01, n), -100 + rng.normal(0, 0.01, n)
        depth = 8 + rng.normal(0, 0.5, n)
        times = np.arange(n) * 30.0
        ref = population("ref", times, lat, lon, depth)
        shifted = population("cand", times, lat + 0.01, lon, depth + 1.0)  # ~1.1 km north, 1 km deeper
        result = pair_distance_error(shifted, ref, match(shifted, ref, 4.0, 15.0), CENTER)
        self.assertGreater(result["pairs"], 0)
        self.assertLess(result["median_km"], 1e-6)

    def test_location_separates_a_common_shift_from_scatter(self):
        # A rigid 2-km eastward shift is all "shift", no "scatter"; a depth pile-up shows in the profile.
        rng = np.random.default_rng(3)
        n = 120
        lat, lon = 40 + rng.normal(0, 0.02, n), -100 + rng.normal(0, 0.02, n)
        times = np.arange(n) * 30.0
        ref = population("ref", times, lat, lon, 5 + rng.normal(0, 1, n))
        east = 2.0 / (111.195 * np.cos(np.radians(40.0)))
        cand = population("cand", times, lat, lon + east, [10.0] * n)
        result = location(cand, ref, match(cand, ref, 4.0, 15.0), CENTER)
        self.assertAlmostEqual(result["shift_east_km"], 2.0, places=1)
        self.assertLess(result["scatter_median_km"], 0.05)
        self.assertEqual(len(result["epi_median_by_period_km"]), 4)
        self.assertEqual(depth_profile(cand)["mode_share"], 1.0)

    def test_magnitude_classes_remove_the_calibration_offset(self):
        # The candidate finds every reference event but reports magnitudes 0.4 low, and adds
        # 10 spurious M2.5 events. After the offset is removed, recall is 1 and precision
        # reflects only the spurious events; the unaligned precision is distorted.
        n = 100
        times = np.arange(n) * 30.0
        mags = np.linspace(1.0, 4.5, n)
        ref = population("authority", times, [40.0] * n, [-100.0] * n, mag=mags, roles="DM")
        extra = np.arange(10) * 30.0 + 5000.0
        cand = population("cand", np.concatenate([times, extra]), [40.0] * (n + 10), [-100.0] * (n + 10),
                          mag=np.concatenate([mags - 0.4, [2.1] * 10]))
        result = magnitude_classes(cand, ref, CENTER)
        self.assertAlmostEqual(result["magnitude_bias"], -0.4, places=6)
        m2 = result["classes"]["M2"]
        self.assertEqual(m2["recall"], 1.0)
        expected = m2["matched"] / (m2["matched"] + 10)
        self.assertAlmostEqual(m2["precision"], expected, places=3)
        self.assertAlmostEqual(m2["dmag"]["mean"], -0.4, places=6)
        self.assertIn("events", result["classes"]["M4"])

    def test_b_value_recovers_a_gutenberg_richter_sample(self):
        rng = np.random.default_rng(4)
        m = np.round(0.95 + rng.exponential(1 / np.log(10), 5000), 1)  # b = 1; bin 1.0 covers [0.95, 1.05)
        self.assertAlmostEqual(b_value(m, 1.0)["b"], 1.0, delta=0.05)

    def test_audit_counts_only_a_complete_review_and_reports_spot_check_agreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            review = Path(tmp)
            labels = pd.DataFrame({"audit_id": ["a01", "a02", "a03", "a04"],
                                   "label": ["earthquake", "not_earthquake", "not_earthquake", ""]})
            labels.to_csv(review / "labels.csv", index=False)
            self.assertIsNone(audited_false_rate(review, 0.4))  # one sample still unlabelled
            labels.loc[3, "label"] = "undecidable"
            labels.to_csv(review / "labels.csv", index=False)
            pd.DataFrame({"audit_id": ["a01", "a02"], "label": ["earthquake", "earthquake"]}).to_csv(
                review / "spot_check.csv", index=False)
            result = audited_false_rate(review, 0.4)
            self.assertAlmostEqual(result["p_false"], 2 / 3, places=4)  # undecidable excluded
            self.assertAlmostEqual(result["rate"], 0.4 * 2 / 3, places=4)
            self.assertEqual(result["spot_check"], {"events": 2, "agreement": 0.5})

    def test_off_structure_uses_other_references_only(self):
        ref = population("ref", [0.0, 10.0], [40.0, 40.0], [-100.0, -100.0], [5.0, 5.0])
        far = population("cand", [0.0], [40.1], [-100.0], [5.0])  # 11 km away
        self.assertEqual(off_structure_fraction(far, [ref], CENTER, 1.0)["fraction"], 1.0)
        self.assertIsNone(off_structure_fraction(ref, [ref], CENTER, 1.0)["fraction"])

    def test_union_support_skips_itself_and_corrects_time_only_chance(self):
        # Event 0 is supported by a located member, event 1 by a time-only member.
        # Event 2 coincides with a time-only event only after the 60-s shift
        # (a chance coincidence), so it is removed from the net fraction.
        cand = population("cand", [0.0, 50.0, 200.0], [40.0] * 3, [-100.0] * 3)
        located = population("loc", [0.0], [40.0], [-100.0])
        time_only = population("tonly", [50.0, 140.0], roles="D", time_only=True)
        result = union_support(cand, [cand, located, time_only])
        self.assertEqual(result["members"], ["loc", "tonly"])
        self.assertAlmostEqual(result["fraction_raw"], 2 / 3, places=4)
        self.assertEqual(result["chance"], 1)
        self.assertAlmostEqual(result["fraction"], 1 / 3, places=4)


if __name__ == "__main__":
    unittest.main()
