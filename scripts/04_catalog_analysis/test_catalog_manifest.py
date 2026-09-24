"""Regression tests for formerly omitted or conflated catalog products."""
import json
import tempfile
import unittest
from pathlib import Path

from build_catalog_manifest import build_manifest, catalog_status, full_product


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

    def test_event_full_filename_is_not_omitted(self):
        product = self.stat('event_full_v1.json', {
            'product_id': 'DataS1_event_catalog', 'selection': 'full',
            'stats': {'row_count': 34091, 'ranges': {}},
        })
        self.assertEqual((product['unit'], product['count']), ('event', 34091))

    def test_phase_only_catalog_is_partial(self):
        product = self.stat('phase_arrivals/full_v1.json', {
            'product_id': 'phase_arrivals', 'kind': 'phase_csv',
            'unit': 'phase_pick', 'selection': 'full',
            'stats': {'kind': 'phase_csv', 'row_count': 6260580},
        })
        self.assertEqual(catalog_status([product]), 'partial')
        self.assertEqual(product['unit'], 'phase_pick')

    def test_phase_rows_not_archive_file_count(self):
        product = self.stat('associated_phase/full_v1.json', {
            'product_id': 'associated_phase', 'kind': 'phase',
            'phase_rows': 1382337, 'file_count': 1165,
        })
        self.assertEqual(product['count'], 1382337)
        self.assertEqual(product['unit'], 'phase_pick')

    def test_moment_tensor_and_approximate_products_are_auxiliary(self):
        for name in ('moment_tensors', 'absolute_approx_v1'):
            with self.subTest(name=name):
                product = self.stat(name + '/full_v1.json', {
                    'product_id': name, 'selection': 'full',
                    'stats': {'row_count': 55, 'ranges': {}},
                })
                self.assertEqual(catalog_status([product]), 'partial')

    def test_metadata_excludes_nonfull_selection(self):
        self.assertIsNone(self.stat('full_v1.json', {
            'selection': 'benchmark', 'stats': {'row_count': 11},
        }))

    def test_window_status_and_all_release_versions_are_preserved(self):
        data = self.root / 'data'
        case = data / 'case'
        (case / 'analysis').mkdir(parents=True)
        (case / 'analysis/processing.yaml').write_text('window_status: not_frozen\n')
        for product, count in [('growclust_corrected', 33328), ('growclust_legacy', 34704)]:
            self.stat(f'data/case/catalogs/C/analysis/stats/{product}/full_v1.json', {
                'product_id': product, 'selection': 'full',
                'stats': {'row_count': count, 'ranges': {}},
            })
        result = build_manifest(data)
        self.assertIn('`not_frozen`', result)
        self.assertIn('33,328', result)
        self.assertIn('34,704', result)
        self.assertNotIn('68,032', result)
        self.assertEqual(result, build_manifest(data))


if __name__ == '__main__':
    unittest.main()
