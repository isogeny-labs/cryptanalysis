#!/usr/bin/env python3
"""Exercise the workflow's sparse patterns against every tracked proof path."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CheckoutCoverageTests(unittest.TestCase):
    def test_actual_git_checkout_preserves_all_proof_inputs(self):
        workflow = (ROOT / ".github/workflows/lean-proof-gate.yml").read_text()
        block = re.search(r"^  LEAN_CHECKOUT: \|\n((?:    .+\n)+)", workflow, re.M)
        self.assertIsNotNone(block)
        patterns = "\n".join(line[4:] for line in block[1].splitlines()) + "\n"
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        # This inventory is independent of the checkout patterns themselves.
        required = {name for name in tracked if name and (
            name.endswith(".lean") or Path(name).name in {
                "lakefile.toml", "lake-manifest.json", "lean-toolchain"}
            or name.startswith("tools/lean/")
            or name == ".github/workflows/lean-proof-gate.yml")}
        self.assertTrue(required)
        with tempfile.TemporaryDirectory(prefix="lean-checkout-coverage-") as temp:
            root = Path(temp)

            def git(*args, **kwargs):
                return subprocess.run(["git", *args], cwd=root, check=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)

            git("init", "--quiet")
            for name in required | {"unrelated-archive/data.json", "unrelated-source/native.cpp"}:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"")
            git("add", ".")
            git("-c", "user.name=Checkout coverage control", "-c", "user.email=control@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Synthetic path inventory")
            git("sparse-checkout", "set", "--no-cone", "--stdin", input=patterns.encode())
            self.assertEqual([], sorted(name for name in required if not (root / name).is_file()))
            self.assertFalse((root / "unrelated-archive/data.json").exists())
            self.assertFalse((root / "unrelated-source/native.cpp").exists())
        # Selection is tested here; the hosted gate still compiles actual sources.
        print(f"checkout retains all {len(required)} tracked proof/context/tool paths")


if __name__ == "__main__":
    unittest.main()
