import unittest

from SeismoAgentBench.scoring import AggregationError, MatchingPolicy, aggregate_catalog_score, score_catalogs


def catalog(event_id, second):
    return {"schema_version": 1, "catalog_id": "catalog", "events": [{
        "event_id": event_id,
        "origin_time": f"2019-07-04T17:00:{second:02d}Z",
        "latitude": 35.7,
        "longitude": -117.5,
        "depth_km": 8.0,
    }]}


class AggregateTests(unittest.TestCase):
    def test_summary_preserves_source_metrics_and_matches(self):
        score = score_catalogs(catalog("candidate", 0), catalog("reference", 1),
                               reference_id="reference", reference_version="1",
                               policy=MatchingPolicy(time_tolerance_s=2))
        summary = aggregate_catalog_score(score)
        self.assertEqual(summary["status"], "aggregated")
        self.assertEqual(summary["metrics"]["detection"]["f1"], 1.0)
        self.assertEqual(summary["source_metrics"], score["metrics"])
        self.assertEqual(summary["matches"], score["matches"])

    def test_unscored_or_incomplete_input_is_rejected(self):
        with self.assertRaisesRegex(AggregationError, "only scored"):
            aggregate_catalog_score({"status": "artifact_invalid"})
        with self.assertRaisesRegex(AggregationError, "missing metrics"):
            aggregate_catalog_score({"status": "scored", "metrics": {}})


if __name__ == "__main__":
    unittest.main()
