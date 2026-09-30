import unittest
from pathlib import Path
import tempfile

from SeismoAgentBench.execution import AuthConfigError, prepare_codex_runtime_home, resolve_auth


class AuthResolutionTests(unittest.TestCase):
    def test_resolves_reference_without_reading_secret(self):
        result = resolve_auth({"auth": {"mode": "env_file", "env_file": "~/private.env"}})
        self.assertEqual(result["mode"], "env_file")
        self.assertTrue(result["env_file"].endswith("/private.env"))

    def test_external_profile_has_no_local_secret_reference(self):
        self.assertEqual(resolve_auth({"auth": {"mode": "external_profile"}}), {
            "mode": "external_profile", "env_file": None, "codex_home": None,
        })

    def test_requires_source_for_file_modes(self):
        with self.assertRaises(AuthConfigError):
            resolve_auth({"auth": {"mode": "codex_home"}})

    def test_copies_private_auth_to_temporary_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "auth-source"
            source.mkdir(mode=0o700)
            source.chmod(0o700)
            auth = source / "auth.json"
            auth.write_text('{"token":"secret"}\n', encoding="utf-8")
            auth.chmod(0o600)
            runtime = root / "runtime"
            runtime.mkdir()
            target = prepare_codex_runtime_home(runtime, source)
            self.assertEqual((target / "auth.json").read_text(), auth.read_text())
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            self.assertEqual((target / "auth.json").stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
