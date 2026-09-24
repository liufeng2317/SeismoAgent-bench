"""Portable source-registry checks using a synthetic case with no evaluation config."""
from pathlib import Path
import tempfile
import subprocess
import sys
import json
import unittest

import yaml

from SeismoAgentBench.utils.source_prepare.catalog import sha256, utc
from SeismoAgentBench.utils.source_prepare.sources import (
    SourceError, case_path, load_case, resolve_stages, select_subset, validate_sources,
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

    def test_cli_preserves_file_state_and_integrity_semantics(self):
        # One public interface covers the same file states without duplicate library assertions.
        cases = [
            ('original', False, 0, 'present', 'not_checked'),
            ('original', True, 0, 'present', 'verified'),
            ('changed', True, 1, 'present', 'mismatch'),
            ('missing', False, 0, 'missing', 'not_checked'),
            ('missing', True, 1, 'missing', 'not_checked'),
        ]
        for state, verify, exit_code, local_status, integrity in cases:
            with self.subTest(state=state, verify=verify):
                payload = self.case / 'source.txt'
                payload.unlink(missing_ok=True)
                if state != 'missing':
                    payload.write_text('synthetic source\n' if state == 'original' else 'changed')
                command = [sys.executable, '-B', '-m', 'SeismoAgentBench.utils.source_prepare',
                           'inventory', '--case-dir', str(self.case)]
                if verify:
                    command.append('--verify-files')
                result = subprocess.run(command, cwd=Path(__file__).resolve().parents[2],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, exit_code, result.stderr)
                row = json.loads(result.stdout)['products']['events']
                self.assertEqual((row['local_status'], row['integrity']), (local_status, integrity))

    def test_paths_allow_internal_links_but_reject_case_escape(self):
        for value in ('../private.txt', '/tmp/private.txt'):
            with self.assertRaises(SourceError):case_path(self.case, value)
        (self.case / 'outside').symlink_to(Path(self.temp.name))
        with self.assertRaises(SourceError):case_path(self.case, 'outside/private.txt')

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
