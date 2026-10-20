import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("audit", Path(__file__).resolve().parents[1] / "audit-deps.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_inventory_does_not_execute_repo_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "analysis.py").write_text("raise RuntimeError('must not execute')\nfrom fpylll import LLL\nimport yaml\n")
            (root / "requirements.txt").write_text("numpy>=1.26\nhttps://user:secret@example.test/pkg\n")
            (root / "Cargo.toml").write_text('[dependencies]\nrayon="1"\nlocal={path="tools/local"}\n')
            ignored = root / "vendor"
            ignored.mkdir()
            (ignored / "skip.py").write_text("import torch\n")
            evidence = audit.inventory(root)["evidence"]
            names = {row["dependency"] for row in evidence}
            self.assertIn("fpylll", names)
            self.assertIn("PyYAML", names)
            self.assertIn("numpy>=1.26", names)
            self.assertNotIn("torch", names)
            self.assertNotIn("local", names)
            self.assertFalse(any("secret" in name for name in names))


if __name__ == "__main__":
    unittest.main()
