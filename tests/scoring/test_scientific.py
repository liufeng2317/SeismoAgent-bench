import unittest

from SeismoAgentBench.scoring import MatchingPolicy, score_catalogs


def event(event_id, second, latitude=35.7, depth=8.0):
    return {
        "event_id": event_id,
        "origin_time": f"2019-07-04T17:00:{second:02d}Z",
        "latitude": latitude,
        "longitude": -117.5,
        "depth_km": depth,
    }


def catalog(events):
    return {"schema_version": 1, "catalog_id": "catalog", "events": events}


class ScientificScoreTests(unittest.TestCase):
    def test_detection_location_and_depth_metrics(self):
        candidate = catalog([event("c-1", 0), event("c-2", 30)])
        reference = catalog([event("r-1", 1, latitude=35.701, depth=9.0), event("r-2", 50)])
        result = score_catalogs(candidate, reference, reference_id="synthetic-ref", reference_version="1",
                                policy=MatchingPolicy(time_tolerance_s=2, horizontal_tolerance_km=1))
        metrics = result["metrics"]
        self.assertEqual(result["status"], "scored")
        self.assertEqual(metrics["matched_events"], 1)
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 0.5)
        self.assertEqual(metrics["f1"], 0.5)
        self.assertAlmostEqual(metrics["depth_error_km"]["mean"], 1.0)
        self.assertGreater(metrics["horizontal_error_km"]["mean"], 0)

    def test_no_matches_preserve_null_error_metrics(self):
        result = score_catalogs(catalog([event("c-1", 0)]), catalog([event("r-1", 30)]),
                                reference_id="synthetic-ref", reference_version="1",
                                policy=MatchingPolicy(time_tolerance_s=1))
        self.assertEqual(result["metrics"]["matched_events"], 0)
        self.assertIsNone(result["metrics"]["horizontal_error_km"]["mean"])
        self.assertEqual(result["metrics"]["precision"], 0.0)
        self.assertEqual(result["metrics"]["recall"], 0.0)


if __name__ == "__main__":
    unittest.main()
