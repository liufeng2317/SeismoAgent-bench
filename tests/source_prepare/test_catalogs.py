"""Catalog meaning and source-specific parser regressions using tiny local fixtures."""
from datetime import timedelta
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from SeismoAgentBench.utils.source_prepare.catalog import event, origin, overlap, utc, within

ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative_path):
    # Only entry scripts outside the importable package need file-based loading.
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manifest = load_script('catalog_manifest', 'scripts/04_catalog_analysis/build_catalog_manifest.py')
ridgecrest = load_script('ridgecrest_audit', 'benchmark_source/2019_ridgecrest_california/scripts/catalogs/audit_references.py')
full_product, catalog_status, build_manifest = manifest.full_product, manifest.catalog_status, manifest.build_manifest
read_events, phase_summary = ridgecrest.read_events, ridgecrest.phase_summary


class CatalogSemanticsTests(unittest.TestCase):
    def row(self, seconds=0, latitude=35.7, longitude=-117.5, depth=5):
        return event(utc('2019-07-04T00:00:00Z')+timedelta(seconds=seconds),
                     latitude, longitude, depth, 1, 'local', 1)


    def test_window_is_half_open_and_mask_is_inclusive(self):
        start=utc('2019-07-04T00:00:00Z');end=start+timedelta(seconds=1)
        bounds={'latitude':[35.7,36.0],'longitude':[-117.5,-117.0],'depth_km':[0,5]}
        self.assertTrue(within(self.row(),start,end,bounds))
        self.assertFalse(within(self.row(1),start,end,bounds))
        self.assertFalse(within(self.row(depth=5.001),start,end,bounds))


    def test_noncanonical_seconds_are_not_silently_normalized(self):
        with self.assertRaises(ValueError):origin(['2019','7','4','0','0','60.1'])
        with self.assertRaises(ValueError):origin(['2019','7','4','0','0','nan'])


    def test_matching_handles_ambiguity_distance_and_native_depth(self):
        cases = [
            ('ambiguous', [self.row(), self.row(.2)], [self.row(.1)], 5, 0, 2),
            ('horizontal_outlier', [self.row()], [self.row(latitude=36.7)], 5, 0, 0),
            ('different_depth_datum', [self.row(depth=5.7)], [self.row(1, depth=5)], 2, 1, 0),
        ]
        for name, left, right, distance, pairs, unresolved in cases:
            with self.subTest(name=name):
                result = overlap(left, right, 1, distance)
                self.assertEqual(result['reciprocal_unique_pairs'], pairs)
                self.assertEqual(result['left_with_candidate_but_unresolved'], unresolved)
                if name == 'ambiguous':
                    self.assertEqual(result['candidate_edges'], 2)
                    self.assertEqual(result['right_multiple_candidates'], 1)
                elif name == 'different_depth_datum':
                    self.assertAlmostEqual(result['native_depth_difference_left_minus_right_km']['p50'], .7)
                else:
                    self.assertEqual(result['candidate_edges'], 0)
                    self.assertEqual(result['left_without_candidate'], 1)


class NativeParserTests(unittest.TestCase):
    def test_malformed_rows_are_recorded_and_liu_has_no_invented_id(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'liu.txt'
            p.write_text('yr mo day hr min sec lat lon dep mag\n2019 7 4 0 0 1.0 35.7 -117.5 5 1\n2019 7 broken\n')
            rows,errors=read_events(p,'liu')
            self.assertEqual(len(rows),1)
            self.assertIsNone(rows[0]['native_id'])
            self.assertEqual(errors[0]['source_row'],3)


    def test_phase_arrivals_use_unix_seconds_and_are_not_events(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'phase.csv'
            start=utc('2019-07-04T00:00:00Z')
            p.write_text('arrival,phase,network,station,template_id,match_id\n'
                         f'{start.timestamp()},P,CI,A,1,2\n'
                         f'{start.timestamp()+1},S,CI,A,1,2\n')
            result=phase_summary(p,start,start+timedelta(seconds=1))
            self.assertEqual(result['row_count'],2)
            self.assertEqual(result['arrival_time_only_rows'],1)
            self.assertEqual(result['match_ids'],1)
            self.assertTrue(result['origin_time_not_supplied'])



class ManifestRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)


    def stat(self, filename, record):
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record))
        return full_product(path)


    def test_product_units_counts_and_roles_are_not_conflated(self):
        cases = [
            ('event_full_v1.json', {'product_id': 'DataS1_event_catalog', 'selection': 'full',
                'stats': {'row_count': 34091, 'ranges': {}}}, 'event', 34091, 'ready'),
            ('phase_arrivals/full_v1.json', {'product_id': 'phase_arrivals', 'kind': 'phase_csv',
                'unit': 'phase_pick', 'selection': 'full', 'stats': {'row_count': 6260580}},
                'phase_pick', 6260580, 'partial'),
            ('associated_phase/full_v1.json', {'product_id': 'associated_phase', 'kind': 'phase',
                'phase_rows': 1382337, 'file_count': 1165}, 'phase_pick', 1382337, 'partial'),
            ('moment_tensors/full_v1.json', {'product_id': 'moment_tensors', 'selection': 'full',
                'stats': {'row_count': 55, 'ranges': {}}}, 'focal_mechanism', 55, 'partial'),
            ('absolute_approx_v1/full_v1.json', {'product_id': 'absolute_approx_v1', 'selection': 'full',
                'stats': {'row_count': 55, 'ranges': {}}}, 'approximate_event', 55, 'partial'),
        ]
        for filename, record, unit, count, status in cases:
            with self.subTest(product=filename):
                product = self.stat(filename, record)
                self.assertEqual((product['unit'], product['count'], catalog_status([product])),
                                 (unit, count, status))

    def test_metadata_excludes_nonfull_selection(self):
        self.assertIsNone(self.stat('full_v1.json', {
            'selection': 'benchmark', 'stats': {'row_count': 11},
        }))


    def test_all_nested_case_catalogs_are_included(self):
        for case, layout in [('first', 'data/catalogs'), ('second', 'data/catalogs')]:
            self.stat(f'benchmark_source/{case}/{layout}/C/analysis/stats/events/full_v1.json', {
                'product_id': 'events', 'selection': 'full',
                'stats': {'row_count': 3, 'ranges': {}},
            })
        result = build_manifest(self.root / 'benchmark_source')
        self.assertIn('./first/data/catalogs/C/README.md', result)
        self.assertIn('./second/data/catalogs/C/README.md', result)


    def test_legacy_layout_is_rejected_instead_of_silently_omitted(self):
        data = self.root / 'benchmark_source'
        (data / 'case/catalogs').mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'data/catalogs'):
            build_manifest(data)


    def test_window_status_and_all_release_versions_are_preserved(self):
        data = self.root / 'benchmark_source'
        case = data / 'case'
        (case / 'analysis').mkdir(parents=True)
        (case / 'analysis/processing.yaml').write_text('window_status: not_frozen\n')
        for product, count in [('growclust_corrected', 33328), ('growclust_legacy', 34704)]:
            self.stat(f'benchmark_source/case/data/catalogs/C/analysis/stats/{product}/full_v1.json', {
                'product_id': product, 'selection': 'full',
                'stats': {'row_count': count, 'ranges': {}},
            })
        result = build_manifest(data)
        self.assertIn('`not_frozen`', result)
        self.assertIn('33,328', result)
        self.assertIn('34,704', result)
        self.assertNotIn('68,032', result)
        self.assertEqual(result, build_manifest(data))



if __name__ == "__main__":
    unittest.main()
