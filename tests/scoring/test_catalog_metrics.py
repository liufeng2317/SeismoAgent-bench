"""Pre-registered catalog metrics v1: matching and metric semantics on synthetic catalogs."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from SeismoAgentBench.scoring.catalog_metrics.audit import audited_false_rate
from SeismoAgentBench.scoring.catalog_metrics.dimensions import b_value, magnitude_classes
from SeismoAgentBench.scoring.catalog_metrics.matching import correspond, match
from SeismoAgentBench.scoring.catalog_metrics.picks_l5 import _collapse_shelly, score_picks_l5
from SeismoAgentBench.scoring.catalog_metrics.metrics import (
    ceilings, depth_profile, location, m90, net_rate, off_structure_fraction, pair_distance_error,
    union_support, versus_final)
from SeismoAgentBench.scoring.catalog_metrics.tables import Population, standardize
from SeismoAgentBench.scoring.catalog_metrics.trust import trust_verdict

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
        self.assertLess(net_rate(len(result["pairs"]), result["chance"], 600), 0.05)


    def test_located_recall_is_chance_corrected(self):
        # A compact, dense swarm: random candidates inside the same box match a
        # located reference by coincidence; the 60-s shifted run removes it (v2).
        rng = np.random.default_rng(3)
        n_ref, n_cand = 2000, 1500
        ref = population("ref", np.sort(rng.uniform(0, 7200, n_ref)), 40 + rng.uniform(0, 0.05, n_ref),
                         -100 + rng.uniform(0, 0.05, n_ref))
        cand = population("cand", np.sort(rng.uniform(0, 7200, n_cand)), 40 + rng.uniform(0, 0.05, n_cand),
                          -100 + rng.uniform(0, 0.05, n_cand))
        result = correspond(cand, ref)
        self.assertEqual(result["gates"], [2.0, 5.0])
        self.assertGreater(len(result["pairs"]) / n_ref, 0.3)  # raw recall looks real
        self.assertLess(net_rate(len(result["pairs"]), result["chance"], n_ref), 0.05)

    def test_chance_correction_keeps_a_complete_dense_catalog_complete(self):
        # Every reference event has its true partner; coincidences add nothing (v1's subtraction would).
        rng = np.random.default_rng(5)
        t = np.sort(rng.uniform(0, 7200, 2000))
        lat, lon = 40 + rng.uniform(0, 0.05, 2000), -100 + rng.uniform(0, 0.05, 2000)
        result = correspond(population("cand", t + 0.2, lat, lon), population("ref", t, lat, lon))
        self.assertGreater(result["chance"], 200)
        self.assertGreater(net_rate(len(result["pairs"]), result["chance"], 2000), 0.97)

    def test_primary_gates_follow_the_reference_then_the_case(self):
        ref = population("ref", [0.0], [40.0], [-100.0])
        cand = population("cand", [3.0], [40.0], [-100.0])
        self.assertEqual(len(correspond(cand, ref)["pairs"]), 0)  # 3 s > the 2-s default
        ref.primary_gates = (4.0, 15.0)
        self.assertEqual(len(correspond(cand, ref)["pairs"]), 1)


class MetricTest(unittest.TestCase):
    def test_versus_final_reports_completeness_precision_and_offsets(self):
        times = np.sort(np.random.default_rng(4).uniform(0, 1e7, 100))  # sparse: no chance coincidence
        final = population("expert_final", times, [40.0] * 100, [-100.0] * 100, [5.0] * 100, roles="")
        cand = population("cand", times[:40] + 0.5, [40.0] * 40, [-100.0] * 40, [3.0] * 40)
        out = versus_final(cand, final, CENTER)
        self.assertAlmostEqual(out["recall"], 0.4)
        self.assertAlmostEqual(out["precision"], 1.0)
        self.assertAlmostEqual(out["event_ratio"], 0.4)
        self.assertAlmostEqual(out["location"]["dz_median_km"], -2.0)
        self.assertAlmostEqual(out["location"]["dt_median_s"], 0.5)
        self.assertAlmostEqual(out["time"]["bias_s"], 0.5)

    def test_ceiling_is_the_best_other_reference(self):
        # Irregular times: a periodic sequence would line up with itself under the 60-s chance shift.
        times = np.sort(np.random.default_rng(2).uniform(0, 100000, 100))
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

    def test_picks_pair_one_to_one_on_common_stations(self):
        ref = pd.DataFrame({"station": ["XX.A", "XX.A", "XX.B", "XX.C"], "phase": ["P", "P", "P", "P"],
                            "time": [100.0, 110.0, 200.0, 300.0]})
        # two candidates near one reference pick: only one pairs; XX.D is not a common station
        cand = pd.DataFrame({"station": ["XX.A", "XX.A", "XX.B", "XX.D"], "phase": ["P", "P", "P", "P"],
                             "time": [100.05, 100.3, 200.4, 300.0]})
        p = score_picks_l5(cand, ref, (0.0, 1000.0))["phases"]["P"]
        self.assertEqual((p["reference"], p["candidate"]), (3, 3))  # XX.C and XX.D drop out
        self.assertEqual((p["matched_0.5s"], p["matched_0.1s"]), (2, 1))

    def test_shelly_release_collapses_to_one_arrival_per_event_station_phase(self):
        # three templates report one detection, a second match_id repeats it 0.2 s later,
        # and a separate earthquake arrives 5 s later
        raw = pd.DataFrame({"match_id": [1, 1, 1, 2, 3], "network": ["WY"] * 5, "station": ["A"] * 5,
                            "phase": ["P"] * 5, "arrival": [10.0, 10.3, 10.1, 10.2, 15.0],
                            "weight": [0.2, 0.9, 0.5, 0.4, 0.7]})
        out = _collapse_shelly(raw)
        self.assertEqual(sorted(out.arrival.round(2)), [10.3, 15.0])

    def test_off_structure_uses_other_references_only(self):
        ref = population("ref", [0.0, 10.0], [40.0, 40.0], [-100.0, -100.0], [5.0, 5.0])
        far = population("cand", [0.0], [40.1], [-100.0], [5.0])  # 11 km away
        self.assertEqual(off_structure_fraction(far, [ref], CENTER, 1.0)["fraction"], 1.0)
        self.assertIsNone(off_structure_fraction(ref, [ref], CENTER, 1.0)["fraction"])

    def test_trust_judges_four_dimensions_and_reports_completeness_apart(self):
        final = {"out_of_mask_fraction": 0.0, "scatter_median_km": 1.5, "off_structure_fraction": 0.01,
                 "depth_mode_share": 0.01, "dmag_median": -0.25, "dmag_std": 0.3, "dmag_slope_per_unit": -0.05,
                 "recall_after_large": 0.8, "recall_other": 0.9, "recall_M4": 1.0}
        good = {"out_of_mask_fraction": 0.05, "audited_false_rate": None, "time_bias_final_s": 0.1,
                "time_mad_final_s": 0.05, "recall_after_large": 0.7, "recall_other": 0.9, "shift_final_km": 0.4,
                "dz_final_km": -0.5, "scatter_final_km": 1.2, "off_structure_fraction": 0.02,
                "depth_mode_share": 0.03, "dmag_median": -0.4, "dmag_std": 0.35, "dmag_slope_per_unit": -0.2,
                "recall_M4": 1.0, "recall_final": 0.3}
        out = trust_verdict(good, final, True)
        self.assertIsNone(out["trusted"])  # only the audit is open
        self.assertEqual(out["dimensions"]["reality"]["verdict"], "pending")
        self.assertEqual(out["dimensions"]["space"]["checks"]["horizontal_scatter"]["threshold"], 1.5)
        self.assertEqual(out["completeness"]["recall_final"], 0.3)  # reported, not judged
        self.assertTrue(trust_verdict({**good, "audited_false_rate": 0.01}, final, True)["trusted"])
        biased = {**good, "audited_false_rate": 0.01, "time_bias_final_s": 1.0, "dz_final_km": -2.2}
        out = trust_verdict(biased, final, True)
        self.assertFalse(out["trusted"])
        self.assertEqual(sorted(out["failed"]), ["depth_bias", "time_bias"])
        self.assertEqual(out["dimensions"]["strength"]["verdict"], "pass")
        self.assertFalse(trust_verdict({}, final, False)["trusted"])

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
        self.assertAlmostEqual(result["fraction"], 0.5, places=4)  # (2/3 - 1/3) / (1 - 1/3)


if __name__ == "__main__":
    unittest.main()


class LeakageReviewTests(unittest.TestCase):
    def test_review_patterns_list_accesses_without_setting_the_flag(self):
        import json
        import tempfile
        from pathlib import Path
        from SeismoAgentBench.scoring.catalog_metrics.process import scan_transcript
        call = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "WebFetch", "input": {"url": "https://scedc.caltech.edu/data/page.html"}}]}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "execution.jsonl"
            path.write_text(json.dumps(call) + "\n", encoding="utf-8")
            out = scan_transcript(path, ["fdsnws/event"], None, [r"scedc\.caltech\.edu/"])
            self.assertFalse(out["flag"])
            self.assertEqual(out["review"], {r"scedc\.caltech\.edu/": {"calls": 1, "first_line": 1}})
            self.assertTrue(scan_transcript(path, [r"scedc\.caltech\.edu/data"], None)["flag"])


class MagnitudeScaleMinimumTests(unittest.TestCase):
    def test_slope_from_few_pairs_is_not_judged(self):
        from SeismoAgentBench.scoring.catalog_metrics.trust import trust_verdict
        final = {"dmag_slope_per_unit": -0.1, "dmag_median": 0.0, "dmag_std": 0.3}
        few = trust_verdict({"dmag_slope_per_unit": None, "dmag_pairs": 12, "dmag_median": 0.0, "dmag_std": 0.3}, final, True)
        self.assertEqual(few["dimensions"]["strength"]["checks"]["magnitude_scale"]["verdict"], "insufficient")
        self.assertNotIn("magnitude_scale", few["failed"])
        none = trust_verdict({"dmag_slope_per_unit": None, "dmag_pairs": 0}, final, True)
        self.assertIn("magnitude_scale", none["failed"])
