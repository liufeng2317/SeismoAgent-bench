"""Prevent accidental disclosure through bundles and weak private-path policies."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[2] / 'evaluations/environment/manage.py'
spec = importlib.util.spec_from_file_location('bench_environment', PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Boundaries(unittest.TestCase):
    def test_staged_elf_loader_is_executable_and_runtime_is_read_only(self):
        # Regression: copyfile stripped ld-linux's execute bits, so chroot
        # execve(Python) failed with EACCES despite an executable Python binary.
        import check_execution_root
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            check_execution_root.stage_python(root)
            loaders = list(root.rglob('ld-linux*.so*'))
            self.assertTrue(loaders, 'Expected the system ELF interpreter')
            for loader in loaders:
                self.assertEqual(loader.stat().st_mode & 0o777, 0o555)
                result = subprocess.run([str(loader), '--verify', str(root/'usr/bin/python3')],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
            for path in root.rglob('*'):
                self.assertFalse(path.stat().st_mode & 0o222, str(path))
                if path.is_dir():
                    self.assertEqual(path.stat().st_mode & 0o111, 0o111)

    def test_bundle_rejects_links_and_private_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            bundle = base / 'public'
            bundle.mkdir()
            (bundle / 'observation.txt').write_text('data')
            module.check_bundle(bundle)
            private = base / 'answer'
            private.write_text('answer')
            (bundle / 'escape').symlink_to(private)
            with self.assertRaises(ValueError):
                module.check_bundle(bundle)
            (bundle / 'escape').unlink()
            for name in ['.env', '.env.local', 'expert', '.git', 'references']:
                with self.subTest(name=name):
                    file = bundle / name
                    file.write_text('private')
                    with self.assertRaises(ValueError):
                        module.check_bundle(bundle)
                    file.unlink()

    def test_policy_requires_existing_private_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            policy = base / 'policy.json'
            file = base / 'hidden.txt'
            file.write_text('answer')
            for denied in [[], [str(base)], [str(base / 'missing')]]:
                with self.subTest(denied=denied):
                    policy.write_text(json.dumps({'allow_read': [str(file)], 'deny_read': denied}))
                    with self.assertRaises(ValueError):
                        module.read_policy(policy)
            policy.write_text(json.dumps({'allow_read': [str(base)], 'deny_read': [str(file)]}))
            self.assertEqual(module.read_policy(policy)['deny_read'], [str(file)])

    def test_access_plan_is_read_only_and_has_explicit_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            data = base / 'data'
            data.mkdir()
            sample = data / 'waveform'
            sample.write_text('data')
            tool = base / 'tool'
            tool.write_text('executable')
            tool.chmod(0o750)
            secret = base / 'secret'
            secret.write_text('private')
            config = base / 'access.json'
            payload = {'account': 'bench-agent01', 'run_id': 'trial-001',
                       'data_read': [{'path': str(data), 'recursive': True}],
                       'tools_read_execute': [{'path': str(tool), 'recursive': False}],
                       'deny_read': [str(secret)]}
            config.write_text(json.dumps(payload))
            modes = {p: p.stat().st_mode for p in [data, sample, tool, secret]}
            plan = module.plan_access(config)
            self.assertFalse(plan['permissions_modified'])
            grants = {x['path']: x['permissions'] for x in plan['grants']}
            self.assertEqual(grants[str(sample)], 'r--')
            self.assertEqual(grants[str(tool)], 'r-x')
            self.assertNotIn(str(base), grants)
            self.assertIn(str(base), plan['ancestor_traversal_candidates'])
            self.assertEqual(modes, {p: p.stat().st_mode for p in modes})
            # Broad parent scopes must not reveal a denied descendant.
            payload['data_read'] = [{'path': str(base), 'recursive': True}]
            config.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):
                module.plan_access(config)
            payload['data_read'] = [{'path': str(data), 'recursive': True}]
            config.write_text(json.dumps(payload))
            (data / 'escape').symlink_to(secret)
            with self.assertRaises(ValueError):
                module.plan_access(config)

    def test_audit_only_run_rejects_grant_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = Path(tmp) / 'policy.json'
            policy.write_text(json.dumps({'allow_read': ['/usr/bin/python3'],
                                          'deny_read': [str(policy)],
                                          'temporary_grants': []}))
            with self.assertRaises(ValueError):
                module.read_policy(policy)

    def test_restriction_cannot_block_public_inputs_or_managed_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            public = base / 'public'
            public.write_text('observation')
            private = base / 'private'
            private.mkdir()
            answer = private / 'answer'
            answer.write_text('answer')
            config = base / 'config.json'
            payload = dict(account='bench-agent01', run_id='restricted-001',
                           data_read=[dict(path=str(public), recursive=False)],
                           tools_read_execute=[], deny_read=[str(answer)],
                           restrict_roots=[str(private)])
            config.write_text(json.dumps(payload))
            self.assertEqual(module.plan_access(config)['restrictions'][0]['permissions'], '---')
            for bad in [base, module.STATE]:
                payload['restrict_roots'] = [str(bad)]
                config.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):
                    module.plan_access(config)

    def test_account_and_run_names_cannot_escape_managed_root(self):
        for name in ['root', 'liufeng1', '../bench-agent01', 'bench-agent01/../../tmp']:
            self.assertIsNone(module.NAME.fullmatch(name))
        for name in ['../escape', '/tmp/run', 'x/y', '']:
            self.assertIsNone(module.RUN_ID.fullmatch(name))
        self.assertIsNotNone(module.NAME.fullmatch('bench-agent01'))
        self.assertIsNotNone(module.RUN_ID.fullmatch('ridgecrest-pilot-001'))


if __name__ == '__main__':
    unittest.main()
