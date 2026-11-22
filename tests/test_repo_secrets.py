from __future__ import annotations

import unittest

from scripts.check_repo_secrets import has_sensitive_value


class SecretScannerRulesTests(unittest.TestCase):
    def test_direct_environment_lookups_are_allowed(self):
        key = b"pass" + b"word="
        self.assertFalse(has_sensitive_value(b"connect(" + key + b'os.environ["DB_PASSWORD"])'))
        self.assertFalse(has_sensitive_value(b"connect(" + key + b'os.environ.get("DB_PASSWORD"))'))
        self.assertFalse(has_sensitive_value(b"connect(" + key + b'os.environ[f"{prefix}_PASSWORD"])'))

    def test_hardcoded_values_and_environment_fallbacks_are_rejected(self):
        key = b"pass" + b"word="
        literal = b'"' + b"local-test-secret-value" + b'"'
        self.assertTrue(has_sensitive_value(key + literal))
        fallback = key + b'os.environ.get("DB_PASSWORD", "local-test-secret-value")'
        self.assertTrue(has_sensitive_value(fallback))

    def test_multiline_and_json_style_assignments_are_rejected(self):
        key = b"pass" + b"word="
        multiline = key + b"\\\n  \"" + b"local-test-secret-value" + b"\""
        self.assertTrue(has_sensitive_value(multiline))
        json_key = b'"pass' + b'word": "' + b"local-test-secret-value" + b'"'
        self.assertTrue(has_sensitive_value(json_key))

    def test_loop_variable_token_does_not_match_across_lines(self):
        self.assertFalse(has_sensitive_value(b"for token in command:\\n    safe.append(token)\\n"))

    def test_placeholder_stays_allowed(self):
        self.assertFalse(has_sensitive_value(b"password=SET_OUT_OF_BAND"))


if __name__ == "__main__":
    unittest.main()
