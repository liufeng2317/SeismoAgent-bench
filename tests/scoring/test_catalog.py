import unittest

from SeismoAgentBench.scoring import CatalogValidationError, validate_catalog


def catalog():
    return {
        "schema_version": 1,
        "catalog_id": "demo",
        "events": [{
            "event_id": "evt-001",
            "origin_time": "2019-07-04T17:00:00Z",
            "latitude": 35.7,
            "longitude": -117.5,
            "depth_km": 8.2,
            "magnitude": 4.1,
            "magnitude_type": "ML",
            "picks": [{
                "pick_id": "pick-001",
                "station_id": "CI.CCC",
                "phase": "P",
                "arrival_time": "2019-07-04T17:00:03Z",
                "probability": 0.98,
            }],
        }],
    }


class CatalogValidationTests(unittest.TestCase):
    def test_valid_catalog_is_accepted(self):
        self.assertEqual(validate_catalog(catalog())["catalog_id"], "demo")

    def test_empty_catalog_is_structurally_valid(self):
        self.assertEqual(validate_catalog({"schema_version": 1, "catalog_id": "empty", "events": []})["events"], [])

    def test_invalid_coordinates_and_timezone_are_rejected(self):
        value = catalog()
        value["events"][0]["latitude"] = 91
        value["events"][0]["origin_time"] = "2019-07-04T17:00:00"
        with self.assertRaisesRegex(CatalogValidationError, "latitude"):
            validate_catalog(value)

    def test_duplicate_event_and_unknown_fields_are_rejected(self):
        value = catalog()
        value["events"].append(dict(value["events"][0]))
        value["events"][0]["unexpected"] = True
        with self.assertRaisesRegex(CatalogValidationError, "unknown field"):
            validate_catalog(value)

    def test_invalid_pick_phase_and_probability_are_rejected(self):
        value = catalog()
        value["events"][0]["picks"][0]["phase"] = "X"
        value["events"][0]["picks"][0]["probability"] = 2
        with self.assertRaisesRegex(CatalogValidationError, "phase"):
            validate_catalog(value)


if __name__ == "__main__":
    unittest.main()
