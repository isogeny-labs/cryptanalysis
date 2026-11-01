import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
INSTALLER = REPO / "ecc2k130/runner/codegen/install_profile_tools.sh"


class ProfileInstallerTests(unittest.TestCase):
    def test_configures_signed_repository_and_installs_pinned_versions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            log = root / "commands.log"
            dispatcher = fake_bin / "dispatcher"
            dispatcher.write_text(
                """#!/bin/bash
set -euo pipefail
name=${0##*/}
printf '%s' "$name" >>"$FAKE_LOG"
printf ' <%s>' "$@" >>"$FAKE_LOG"
printf '\n' >>"$FAKE_LOG"
case "$name" in
  id)
    printf '0\n'
    ;;
  dpkg)
    if [[ ${1:-} == --print-architecture ]]; then printf 'amd64\n'; fi
    ;;
  mktemp)
    mkdir "$FAKE_TMP_ROOT/work"
    printf '%s\n' "$FAKE_TMP_ROOT/work"
    ;;
  curl)
    while (($#)); do
      if [[ $1 == --output ]]; then printf 'fixture' >"$2"; break; fi
      shift
    done
    ;;
  sha256sum)
    input=$(cat)
    printf 'sha256-input <%s>\n' "$input" >>"$FAKE_LOG"
    ;;
  apt-cache)
    exit 0
    ;;
esac
"""
            )
            dispatcher.chmod(0o755)
            for name in (
                "id", "dpkg", "mktemp", "curl", "sha256sum", "apt-get",
                "apt-cache", "dpkg-query",
            ):
                (fake_bin / name).symlink_to(dispatcher)

            environment = os.environ.copy()
            environment.update(
                PATH=f"{fake_bin}:{environment['PATH']}",
                FAKE_LOG=str(log),
                FAKE_TMP_ROOT=str(root),
            )
            completed = subprocess.run(
                ["bash", str(INSTALLER)],
                cwd=REPO,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            commands = log.read_text()
            self.assertIn(
                "curl <--proto> <=https> <--tlsv1.2> <--fail> <--location> <--silent> "
                "<--show-error>",
                commands,
            )
            self.assertIn("cuda-keyring_1.1-1_all.deb", commands)
            self.assertIn(
                "d2a6b11c096396d868758b86dab1823b25e14d70333f1dfa74da5ddaf6a06dba",
                commands,
            )
            self.assertIn(
                "apt-cache <show> "
                "<nsight-systems-2026.3.2=2026.3.2.476-263238834031v0>",
                commands,
            )
            self.assertIn(
                "apt-cache <show> "
                "<nsight-compute-2026.3.1=2026.3.1.2-1>",
                commands,
            )
            self.assertIn(
                "apt-get <install> <-y> <--no-install-recommends> "
                "<build-essential> <python3> "
                "<nsight-systems-2026.3.2=2026.3.2.476-263238834031v0> "
                "<nsight-compute-2026.3.1=2026.3.1.2-1>",
                commands,
            )


if __name__ == "__main__":
    unittest.main()
