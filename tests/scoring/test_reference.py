import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.scoring import MatchingPolicy, ReferenceError, ReferenceSpec, match_events


def catalog(offset=0.0):
    return {
        "schema_version": 1,
        "catalog_id": "catalog",
        "events": [{
            "event_id": "evt-001",
            "origin_time": f"2019-07-04T17:00:{offset:04.1f}Z",
            "latitude": 35.7,
            "longitude": -117.5,
            "depth_km": 8.0,
        }],
    }


class ReferenceTests(unittest.TestCase):
    def test_manifest_loads_reference_identity_and_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_path = root / "reference.json"
            manifest_path = root / "reference_manifest.json"
            catalog_path.write_text(json.dumps(catalog()), encoding="utf-8")
            manifest_path.write_text(json.dumps({
                "schema_version": 1, "reference_id": "official", "version": "1",
                "role": "absolute-location", "path": str(catalog_path),
            }), encoding="utf-8")
            spec = ReferenceSpec.from_manifest(manifest_path)
            self.assertEqual(spec.record()["role"], "absolute-location")
            self.assertEqual(len(spec.load_catalog()["events"]), 1)

    def test_manifest_resolves_relative_catalog_path_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reference.json").write_text(json.dumps(catalog()), encoding="utf-8")
            manifest = root / "reference_manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": 1, "reference_id": "relative", "version": "1",
                "role": "smoke", "path": "reference.json",
            }), encoding="utf-8")
            spec = ReferenceSpec.from_manifest(manifest)
            self.assertEqual(spec.path, root / "reference.json")
            self.assertEqual(len(spec.load_catalog()["events"]), 1)

    def test_matching_is_one_to_one_and_records_distances(self):
        result = match_events(catalog(), catalog(1.0), MatchingPolicy(time_tolerance_s=2))
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["candidate_event_id"], "evt-001")
        self.assertEqual(result["unmatched_reference_event_ids"], [])

    def test_outside_tolerance_is_unmatched(self):
        result = match_events(catalog(), catalog(10.0), MatchingPolicy(time_tolerance_s=2))
        self.assertEqual(result["matches"], [])
        self.assertEqual(result["unmatched_candidate_event_ids"], ["evt-001"])

    def test_invalid_manifest_and_policy_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            manifest.write_text(json.dumps({"schema_version": 1, "reference_id": "ref"}), encoding="utf-8")
            with self.assertRaises(ReferenceError):
                ReferenceSpec.from_manifest(manifest)
        with self.assertRaises(ReferenceError):
            MatchingPolicy(time_tolerance_s=0)


if __name__ == "__main__":
    unittest.main()
