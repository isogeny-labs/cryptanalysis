import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
INSTALLER = REPO / "ecc2k130/runner/codegen/extract_nsys_tools_v11.sh"
INSTALLER_V12 = REPO / "ecc2k130/runner/codegen/extract_nsys_tools_v12.sh"
LEGACY_INSTALLER = REPO / "ecc2k130/runner/codegen/install_nsys_tools.sh"


class ProfileExtractorTests(unittest.TestCase):
    def test_legacy_installer_remains_byte_identical_for_existing_callers(self):
        import hashlib
        self.assertEqual(
            hashlib.sha256(LEGACY_INSTALLER.read_bytes()).hexdigest(),
            "50a0a564f4c370b9279a49a4e385fd1a6f06408a21e72e4bd1e4b0918c333aa9",
        )

    def test_exact_deb_is_extracted_without_package_manager_mutation(self):
        text = INSTALLER.read_text(encoding="utf-8")
        self.assertIn(
            "nsight-systems-2026.3.2_2026.3.2.476-1_amd64.deb", text,
        )
        self.assertIn(
            "e9bf0ff9c613ff5545095a4177676a9579cb666e78c8621c3792f3559e2c1690",
            text,
        )
        self.assertIn("systems_deb_bytes='448261416'", text)
        self.assertIn("systems_version='2026.3.2.476-263238834031v0'", text)
        self.assertIn(
            "systems_binary_sha256='68a5fb843322bda1b090900a0297b9d5bee43daf8b870a809a6f8aa93059ae16'",
            text,
        )
        self.assertIn("systems_binary_bytes='87282816'", text)
        self.assertIn("/usr/bin/dpkg-deb --extract", text)
        self.assertIn("/usr/bin/dpkg-deb --field", text)
        for forbidden in (
            "apt-get", "apt-cache", "dpkg --install", "dpkg -i", "cuda-keyring",
            "DEBIAN_FRONTEND", "build-essential", "pip install",
        ):
            self.assertNotIn(forbidden, text)

        syntax = subprocess.run(
            ["/usr/bin/bash", "-n", str(INSTALLER)], cwd=REPO,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(syntax.returncode, 0, syntax.stderr)

    def test_refuses_destination_outside_fresh_task_root_before_download(self):
        completed = subprocess.run(
            ["/usr/bin/bash", str(INSTALLER), "/tmp/not-a-v11-task/nsys-package"],
            cwd=REPO, capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("outside the fresh v11 task root", completed.stderr)

    def test_v12_extractor_is_equivalent_but_namespace_closed(self):
        v11 = INSTALLER.read_text(encoding="utf-8")
        v12 = INSTALLER_V12.read_text(encoding="utf-8")
        self.assertEqual(v12, v11.replace("v11", "v12"))
        syntax = subprocess.run(
            ["/usr/bin/bash", "-n", str(INSTALLER_V12)], cwd=REPO,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        completed = subprocess.run(
            ["/usr/bin/bash", str(INSTALLER_V12), "/tmp/not-a-v12-task/nsys-package"],
            cwd=REPO, capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("outside the fresh v12 task root", completed.stderr)


if __name__ == "__main__":
    unittest.main()
