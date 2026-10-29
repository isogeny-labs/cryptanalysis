import hashlib
from pathlib import Path
import tempfile
import unittest

from check_quartic_certificates import audit_axioms, verify_inputs


class CertificateRefusalTests(unittest.TestCase):
    def test_changed_or_missing_frozen_input_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "certificate.json").write_bytes(b"original")
            expected = {"certificate.json": hashlib.sha256(b"original").hexdigest()}
            self.assertEqual(verify_inputs(root, expected), [])
            (root / "certificate.json").write_bytes(b"changed")
            self.assertEqual(verify_inputs(root, expected)[0]["error"], "digest mismatch")
            (root / "certificate.json").unlink()
            self.assertEqual(verify_inputs(root, expected)[0]["error"], "missing")

    def test_parent_and_symlink_escape_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            outside = root.parent / "outside"
            outside.write_bytes(b"secret")
            (root / "link").symlink_to(outside)
            for name in ("../outside", "link"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    verify_inputs(root, {name: hashlib.sha256(b"secret").hexdigest()})

    def test_missing_or_claim_axioms_cannot_replace_a_proof(self):
        source = "#print axioms Example.result\n"
        self.assertEqual(audit_axioms(source, "'Example.result' depends on axioms: [propext]"), 1)
        for output in ("", "'Example.result' depends on axioms: [sorryAx]",
                       "'Example.result' depends on axioms: [ClaimAssumed]"):
            with self.subTest(output=output), self.assertRaises(ValueError):
                audit_axioms(source, output)


if __name__ == "__main__":
    unittest.main()
