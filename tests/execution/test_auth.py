import unittest

from SeismoAgentBench.execution import AuthConfigError, resolve_auth


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


if __name__ == "__main__":
    unittest.main()
