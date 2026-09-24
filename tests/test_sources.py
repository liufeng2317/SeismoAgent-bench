"""Portable source-registry checks using a synthetic case with no evaluation config."""
from pathlib import Path
import tempfile
import subprocess
import sys
import json
import unittest

import yaml

from seismoagentbench.catalog import sha256, utc
from seismoagentbench.sources import (
    SourceError, case_path, inventory, load_case, resolve_stages, select_subset, validate_sources,
)


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.case = Path(self.temp.name) / 'synthetic_case'
        (self.case / 'analysis').mkdir(parents=True)
        (self.case / 'README.md').write_text('Synthetic provenance\n')
        source = self.case / 'source.txt'
        source.write_text('synthetic source\n')
        self.cfg = {
            'schema_version': 2, 'case_id': self.case.name,
            'source_groups': {'PUBLIC_RELEASE': {'readme': 'README.md'}},
            'sources': {'events': {
                'source_ref': 'PUBLIC_RELEASE', 'path': 'source.txt',
                'expected_sha256': sha256(source), 'unit': 'event',
                'format': 'text', 'parser': 'synthetic', 'version': 'v1',
            }},
        }
        self.save()

    def save(self):
        (self.case / 'analysis/processing.yaml').write_text(yaml.safe_dump(self.cfg))

    def test_source_registry_does_not_require_experiment_or_evaluation_fields(self):
        cfg = load_case(self.case)
        report = inventory(cfg, self.case, verify=True)
        self.assertEqual(report['products']['events']['integrity'], 'verified')
        self.assertNotIn('formal_evaluation_ready', report)

    def test_cli_reports_integrity_failures_with_nonzero_exit(self):
        (self.case / 'source.txt').write_text('changed')
        result = subprocess.run([sys.executable, '-B', '-m', 'seismoagentbench',
            'validate-sources', '--case-dir', str(self.case), '--verify-files'],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['mismatched_products'], ['events'])

    def test_cli_can_inventory_missing_payload_without_claiming_verification(self):
        (self.case / 'source.txt').unlink()
        result = subprocess.run([sys.executable, '-B', '-m', 'seismoagentbench',
            'inventory', '--case-dir', str(self.case)],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        row = json.loads(result.stdout)['products']['events']
        self.assertEqual((row['local_status'], row['integrity']), ('missing', 'not_checked'))

    def test_inventory_without_hashing_does_not_claim_integrity(self):
        report = inventory(self.cfg, self.case)
        self.assertEqual(report['products']['events']['integrity'], 'not_checked')

    def test_changed_and_missing_local_payloads_are_distinct(self):
        (self.case / 'source.txt').write_text('changed')
        self.assertEqual(inventory(self.cfg, self.case, True)['products']['events']['integrity'], 'mismatch')
        (self.case / 'source.txt').unlink()
        self.assertEqual(inventory(self.cfg, self.case, True)['products']['events']['local_status'], 'missing')
        validate_sources(self.cfg, self.case)  # The release metadata is still a valid contract.

    def test_paths_cannot_escape_case(self):
        for value in ('../private.txt', '/tmp/private.txt'):
            with self.assertRaises(SourceError):case_path(self.case, value)
        (self.case / 'outside').symlink_to(Path(self.temp.name))
        with self.assertRaises(SourceError):case_path(self.case, 'outside/private.txt')

    def test_internal_symlink_is_supported(self):
        (self.case / 'alias.txt').symlink_to('source.txt')
        self.assertEqual(case_path(self.case, 'alias.txt'), self.case / 'source.txt')

    def test_unknown_units_groups_and_hashes_are_rejected(self):
        product = self.cfg['sources']['events']
        for key, value in [('unit', 'rows'), ('source_ref', 'missing'), ('expected_sha256', 'bad')]:
            old = product[key]; product[key] = value
            with self.assertRaises(SourceError):validate_sources(self.cfg, self.case)
            product[key] = old

    def test_legacy_metadata_is_not_silently_upgraded(self):
        self.cfg['schema_version'] = 1
        with self.assertRaisesRegex(SourceError, 'explicit source-registry migration'):
            validate_sources(self.cfg, self.case)

    def test_duplicate_yaml_keys_are_rejected(self):
        with (self.case / 'analysis/processing.yaml').open('a') as f:f.write('\nschema_version: 2\n')
        with self.assertRaisesRegex(SourceError, 'Duplicate YAML key'):load_case(self.case)

    def test_source_subsets_preserve_records_and_reject_missing_fields(self):
        rows = [{'nbranch': 1}, {'nbranch': 2}, {'nbranch': 3}]
        subset = select_subset(rows, {'field': 'nbranch', 'operator': 'gt', 'value': 1})
        self.assertEqual(subset, rows[1:])
        self.assertEqual(len(rows), 3)
        with self.assertRaises(SourceError):select_subset([{}], {'field': 'nbranch', 'operator': 'eq', 'value': 1})

    def test_generic_stage_partition_and_invalid_order(self):
        design = {'candidate_window': {'start_utc': '2020-01-01T00:00:00Z', 'end_utc': '2020-01-03T00:00:00Z'}}
        audit = {'stage_names': ['before', 'after'], 'stage_boundaries': [
            {'anchor': 'window_start'}, {'anchor': 'transition'}, {'anchor': 'window_end'}]}
        stages = resolve_stages(design, audit, {'transition': utc('2020-01-02T00:00:00Z')})
        self.assertEqual([s[0] for s in stages], ['before', 'after'])
        self.assertEqual(stages[0][2], stages[1][1])
        with self.assertRaisesRegex(SourceError, 'strictly increase'):
            resolve_stages(design, audit, {'transition': utc('2020-01-04T00:00:00Z')})


if __name__ == '__main__':
    unittest.main()
