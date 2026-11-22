"""Regression tests for per-attempt receipt preservation and failure status."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class AttemptReceipts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "audit"
        self.root.mkdir()
        shutil.copy2(HERE / "run.py", self.root / "run.py")
        shutil.copy2(HERE / "scan.py", self.root / "scan.py")
        names = ("runtime-info.json", "scan.stdout", "scan.stderr", "launch.json", "scan.json")
        for name in names:
            (self.root / name).write_text("original evidence\n")
        self.sage = Path(self.tmp.name) / "fake-sage"
        self.sage.write_text("""#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
if sys.argv[1:] == ['--runtime-info']:
    print(json.dumps({'runtime': 'fake'}))
    raise SystemExit(0)
output = Path(sys.argv[sys.argv.index('--output') + 1])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({'status': 'fake'}) + '\\n')
print('scan stdout')
print('scan stderr', file=sys.stderr)
raise SystemExit(int(os.environ.get('FAKE_SCAN_EXIT', '0')))
""")
        self.sage.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def run_attempt(self, exit_code):
        env = dict(os.environ, HECKE_SAGE=str(self.sage), FAKE_SCAN_EXIT=str(exit_code))
        return subprocess.run([sys.executable, str(self.root / "run.py")],
                              capture_output=True, text=True, env=env)

    def test_each_attempt_is_retained_and_failed_child_fails_launcher(self):
        failed = self.run_attempt(23)
        self.assertEqual(failed.returncode, 23, failed.stdout + failed.stderr)
        first = next((self.root / "runs").iterdir())
        first_receipt = json.loads((first / "launch.json").read_text())
        self.assertEqual(first_receipt["exit_code"], 23)
        self.assertEqual((first / "scan.stdout").read_text().strip(), "scan stdout")
        self.assertEqual((first / "scan.stderr").read_text().strip(), "scan stderr")

        passed = self.run_attempt(0)
        self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)
        attempts = sorted((self.root / "runs").iterdir())
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(attempts[0].name, attempts[1].name)
        self.assertEqual(json.loads((attempts[1] / "launch.json").read_text())["exit_code"], 0)
        names = ("runtime-info.json", "scan.stdout", "scan.stderr", "launch.json", "scan.json")
        for name in names:
            self.assertEqual((self.root / name).read_text(), "original evidence\n")


if __name__ == '__main__':
    unittest.main()
