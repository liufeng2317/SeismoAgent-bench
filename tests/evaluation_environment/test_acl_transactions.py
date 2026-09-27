"""Real disposable-file ACL tests; these do not claim cross-UID root validation."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'evaluations/environment/acl_transaction.py'
spec = importlib.util.spec_from_file_location('acl_transaction', SOURCE)
aclmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aclmod)


class ACLTransactions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.files = [self.base / 'a', self.base / 'b']
        for p in self.files:
            p.write_text('data')
            p.chmod(0o600)
        self.uid = 65534 if os.getuid() != 65534 else 65533
        self.tx = aclmod.Transaction(self.base / 'journal.json')
        self.targets = [{'path': str(p), 'permissions': 'r--'} for p in self.files]

    def text(self, p):
        with aclmod.open_target(p) as fd:
            return self.tx.acl.get(fd)

    def test_grant_restores_absent_and_existing_entry_and_mode(self):
        for existing in (False, True):
            with self.subTest(existing=existing):
                p = self.files[0]
                if existing:
                    with aclmod.open_target(p) as fd:
                        self.tx.acl.convert(f'user::rw-\nuser:{self.uid}:---\ngroup::---\nmask::r--\nother::---\n', fd)
                before, mode = self.text(p), p.stat().st_mode
                tx = aclmod.Transaction(self.base / f'journal-{existing}.json')
                tx.prepare(self.targets[:1], self.uid)
                tx.apply()
                self.assertEqual(aclmod.fields(self.text(p))[f'user:{self.uid}'], 'r--')
                tx.restore()
                self.assertEqual(self.text(p), before)
                self.assertEqual(p.stat().st_mode, mode)

    def test_failure_after_second_syscall_rolls_back_both_files(self):
        before = [self.text(p) for p in self.files]
        self.tx.prepare(self.targets, self.uid)
        original = self.tx.acl.convert
        calls = 0
        def fail(text, fd=None):
            nonlocal calls
            result = original(text, fd)
            if fd is not None:
                calls += 1
                if calls == 2:
                    raise OSError('injected post-syscall failure')
            return result
        with patch.object(self.tx.acl, 'convert', side_effect=fail):
            with self.assertRaises(OSError):
                self.tx.apply()
        self.assertEqual(self.tx.record['state'], 'restored')
        self.assertEqual([self.text(p) for p in self.files], before)

    def test_directory_restriction_preserves_other_entries_and_restores(self):
        p = self.base / 'private'
        p.mkdir(mode=0o755)
        before, mode = self.text(p), p.stat().st_mode
        self.tx.prepare([{'path': str(p), 'permissions': '---'}], self.uid)
        self.tx.apply()
        fields = aclmod.fields(self.text(p))
        self.assertEqual(fields[f'user:{self.uid}'], '---')
        for key, value in aclmod.fields(before).items():
            self.assertEqual(fields[key], value)
        self.tx.restore()
        self.assertEqual(self.text(p), before)
        self.assertEqual(p.stat().st_mode, mode)

    def test_process_exit_between_syscall_and_journal_is_recoverable(self):
        before = self.text(self.files[0])
        self.tx.prepare(self.targets[:1], self.uid)
        code = '''import sys,os
sys.path.insert(0,sys.argv[1])
from acl_transaction import Transaction
t=Transaction(sys.argv[2]);original=t.acl.convert
def crash(text,fd=None):
 result=original(text,fd)
 if fd is not None: os._exit(42)
 return result
t.acl.convert=crash
t.apply()
'''
        result = subprocess.run([sys.executable, '-c', code, str(SOURCE.parent), str(self.tx.path)])
        self.assertEqual(result.returncode, 42)
        recovered = aclmod.Transaction(self.tx.path)
        self.assertEqual(recovered.record['entries'][0]['status'], 'intent')
        recovered.restore()
        self.assertEqual(self.text(self.files[0]), before)

    def test_mask_widening_rejected_before_any_mutation(self):
        p = self.files[1]
        with aclmod.open_target(p) as fd:
            self.tx.acl.convert('user::rw-\ngroup::---\nmask::---\nother::---\n', fd)
        before = [self.text(p) for p in self.files]
        with self.assertRaises(ValueError):
            self.tx.prepare(self.targets, self.uid)
        self.assertEqual([self.text(p) for p in self.files], before)
        self.assertFalse(self.tx.path.exists())

    def test_external_acl_change_is_not_overwritten(self):
        self.tx.prepare(self.targets[:1], self.uid)
        self.tx.apply()
        p = self.files[0]
        with aclmod.open_target(p) as fd:
            modified = self.tx.acl.get(fd).replace('other::---', 'other::r--')
            self.tx.acl.convert(modified, fd)
        before = self.text(p)
        with self.assertRaises(RuntimeError):
            self.tx.restore()
        self.assertEqual(self.text(p), before)
        self.assertEqual(self.tx.record['state'], 'recovery_required')

    def test_native_acl_failure_does_not_fall_back_to_mode_changes(self):
        before = self.text(self.files[0])
        mode = self.files[0].stat().st_mode
        self.tx.prepare(self.targets[:1], self.uid)
        original = self.tx.acl.convert
        def unsupported(text, fd=None):
            if fd is not None:
                raise OSError(95, 'ACL not supported')
            return original(text)
        with patch.object(self.tx.acl, 'convert', side_effect=unsupported):
            with self.assertRaises(OSError):
                self.tx.apply()
        self.assertEqual(self.text(self.files[0]), before)
        self.assertEqual(self.files[0].stat().st_mode, mode)
        self.assertEqual(self.tx.record['state'], 'restored')

    def test_replacement_inode_is_not_modified(self):
        self.tx.prepare(self.targets[:1], self.uid)
        self.tx.apply()
        p = self.files[0]
        p.rename(self.base/'original')
        p.write_text('replacement')
        before = self.text(p)
        with self.assertRaises(RuntimeError):
            self.tx.restore()
        self.assertEqual(self.text(p), before)


if __name__ == '__main__':
    unittest.main()
